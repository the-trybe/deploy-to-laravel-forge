import copy
import logging
import os
import sys
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

from forge_api import ForgeApi
from utils import (
    cat_paths,
    format_php_version,
    parse_env,
    replace_nginx_variables,
    replace_secrets_and_envs_yaml,
    validate_yaml_data,
    wait,
)

load_dotenv()

DEBUG = (
    os.getenv("DEBUG", "false").lower() == "true" or os.getenv("RUNNER_DEBUG") == "1"
)
SOURCE_REPO_PATH = os.getenv(
    "GITHUB_WORKSPACE", "./"
)  # represents the path to the repository that triggered the GitHub Action
DEPLOYMENT_FILE_NAME = os.getenv("DEPLOYMENT_FILE", None)
FORGE_API_TOKEN = os.getenv("FORGE_API_TOKEN")
SECRETS_ENV = os.getenv("SECRETS", None)

logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    action_dir = cat_paths(
        os.path.dirname(__file__), "../"
    )  # path of the action directory (parent directory of this file)
    forge_uri = "https://forge.laravel.com/api"
    if FORGE_API_TOKEN is None or FORGE_API_TOKEN == "":
        raise Exception("FORGE_API_TOKEN is not set")

    # Determine deployment file path
    if DEPLOYMENT_FILE_NAME:
        dep_file_path = cat_paths(SOURCE_REPO_PATH, DEPLOYMENT_FILE_NAME)
    else:
        # Check for both .yml and .yaml extensions
        yml_path = cat_paths(SOURCE_REPO_PATH, "forge-deploy.yml")
        yaml_path = cat_paths(SOURCE_REPO_PATH, "forge-deploy.yaml")

        if os.path.exists(yml_path):
            dep_file_path = yml_path
        elif os.path.exists(yaml_path):
            dep_file_path = yaml_path
        else:
            raise Exception(
                "No deployment file found. Please create either 'forge-deploy.yml' or 'forge-deploy.yaml'"
            )

    try:
        with open(dep_file_path, "r") as file:
            data = yaml.safe_load(file)
            logger.debug("YAML data: %s", data)
    except FileNotFoundError as e:
        raise Exception(f"The configuration file {dep_file_path} is missing.") from e
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML file: {e}") from e

    # replace secrets
    secrets = None
    if SECRETS_ENV:
        secrets = parse_env(SECRETS_ENV)

    try:
        data: dict = replace_secrets_and_envs_yaml(data, secrets)  # type: ignore
    except Exception as e:
        raise Exception(f"Error replacing secrets: {e}") from e

    config = validate_yaml_data(data)

    forge_api = ForgeApi(FORGE_API_TOKEN, config["organization"])

    server = forge_api.get_server_by_name(config["server"])
    server_id = server.get("id", None)

    if not server_id:
        raise Exception(f"Server `{config["server"]}` not found")

    # sites
    server_sites = forge_api.get_all_sites(server_id)

    for site_conf in config["sites"]:
        print("\n")

        # Compute domain_name based on domain_mode
        site_conf["domain_name"] = (
            site_conf["name"]
            if site_conf["domain_mode"] == "custom"
            else f"{site_conf['name']}.on-forge.com"
        )

        logger.info(f"\t---- Site: {site_conf['domain_name']} ----")

        existing_site = next(
            (
                site
                for site in server_sites
                if site["attributes"]["name"] == site_conf["domain_name"]
            ),
            None,
        )

        # install site's php version in server
        if site_conf.get("php_version"):
            # check if version is installed, if not install it
            server_php_versions = forge_api.get_server_installed_php_versions(server_id)
            if format_php_version(site_conf.get("php_version")) not in [
                php["attributes"]["binary_name"] for php in server_php_versions
            ]:
                logger.info(f"Installing php version {site_conf.get('php_version')}...")
                try:
                    forge_api.install_php_version(
                        server_id, site_conf.get("php_version")
                    )

                    # wait for installation
                    def until_php_installed():
                        installed_php = forge_api.get_php_version(
                            server_id, site_conf.get("php_version")
                        )
                        if not installed_php:
                            raise Exception("Php version not found after installation")
                        return installed_php["attributes"]["status"] == "installed"

                    if not wait(until_php_installed):
                        raise Exception("Php installation timed out")
                except Exception as e:
                    raise Exception(f"Failed to install php version: {e}") from e

                logger.info(f"Php version {site_conf.get('php_version')} installed")

        # create site
        if not existing_site:
            # nginx template

            nginx_template_id = None
            if site_conf.get("nginx_template"):
                nginx_templates = forge_api.get_nginx_templates_by_name(
                    server_id, site_conf["nginx_template"]
                )
                nginx_template_id = (
                    nginx_templates.get("id") if nginx_templates else None
                )

                # if template isn't added in the server add it from nginx-templates folder
                if not nginx_template_id:
                    nginx_template_path = cat_paths(
                        action_dir,
                        "nginx_templates/",
                        f"{site_conf['nginx_template']}.conf",
                    )
                    logger.info("Nginx template not created in the server")
                    logger.info("Creating nginx template...")
                    if os.path.exists(nginx_template_path):
                        with open(
                            nginx_template_path,
                            "r",
                        ) as file:
                            nginx_template_id = forge_api.create_nginx_template(
                                server_id, site_conf["nginx_template"], file.read()
                            )
                            logger.info("Nginx template created successfully")
                    else:
                        raise Exception("Invalid nginx template name")

            # Normalize shared paths to have both 'from' and 'to'
            # TODO: if forge adds a way to update shared paths after site creation implement it
            shared_paths_normalized = []
            for path in site_conf["shared_paths"]:
                if isinstance(path, str):
                    # String format: use same path for both from and to
                    shared_paths_normalized.append({"from": path, "to": path})
                elif isinstance(path, dict):
                    # Dict format: already has from and to
                    shared_paths_normalized.append(
                        {"from": path["from"], "to": path["to"]}
                    )

            create_site_payload = {
                "name": site_conf["name"],
                "domain_mode": site_conf["domain_mode"],
                "www_redirect_type": site_conf["www_redirect_type"],
                "allow_wildcard_subdomains": False,
                "type": site_conf["project_type"],
                "web_directory": cat_paths(site_conf["root_dir"], site_conf["web_dir"]),
                "is_isolated": site_conf["isolated"],
                "isolated_user": site_conf.get("isolated_user"),
                "nginx_template_id": nginx_template_id,
                "push_to_deploy": False,
                "php_version": site_conf.get("php_version"),
                "zero_downtime_deployments": site_conf["zero_downtime_deployments"],
                "shared_paths": (
                    shared_paths_normalized
                    if len(shared_paths_normalized) > 0
                    else None
                ),
            }

            create_site_payload = {
                k: v for k, v in create_site_payload.items() if v is not None
            }  # Remove None values

            # add repository
            if site_conf["clone_repository"]:

                create_site_payload["source_control_provider"] = "github"
                create_site_payload["repository"] = config["github_repository"]
                create_site_payload["branch"] = (
                    site_conf.get("github_branch") or config["github_branch"]
                )
                create_site_payload["install_composer_dependencies"] = site_conf[
                    "install_composer_dependencies"
                ]

            # create site
            logger.info("Creating site...")
            existing_site = forge_api.create_site(server_id, create_site_payload)

            def until_site_installed():
                site = forge_api.get_site_by_id(server_id, existing_site["id"])
                return site["attributes"]["status"] == "installed" and (
                    not site_conf["clone_repository"]
                    or site["attributes"]["repository"]["status"] == "installed"
                )

            if not wait(until_site_installed):
                raise Exception("Adding repository timed out")

            logger.info("Site created successfully")

            # set site nginx variables
            try:
                nginx_config = forge_api.get_nginx_config(
                    server_id, existing_site["id"]
                )["attributes"]["content"]
                nginx_config = replace_nginx_variables(
                    nginx_config, site_conf["nginx_template_variables"]
                )
                forge_api.set_nginx_config(server_id, existing_site["id"], nginx_config)
            except Exception as e:
                raise Exception(f"Failed to set nginx config variables: {e}") from e

        else:
            logger.info("Site already exists")

        site_id = existing_site["id"]
        logger.debug(f"Site: %s", existing_site)

        # ---- update aliases ----
        try:
            # TODO: change aliases to extra_domains (or smtng like that) and add www redirect type option
            existing_domains = forge_api.get_site_domains(server_id, site_id)
            existing_domains_list = [
                domain["attributes"]["name"]
                for domain in existing_domains
                if domain["attributes"]["type"] != "primary"
            ]
            config_aliases = site_conf["aliases"]

            # If aliases are not the same, sync them
            if set(existing_domains_list) != set(config_aliases):
                # Delete domains that exist in site but not in config
                for domain in existing_domains:
                    domain_name = domain["attributes"]["name"]
                    if (
                        domain["attributes"]["type"] != "primary"
                        and domain_name not in config_aliases
                    ):
                        forge_api.delete_site_domain(server_id, site_id, domain["id"])
                        logger.info(f"Domain '{domain_name}' deleted from site.")

                # Create domains that exist in config but not in site
                for alias in config_aliases:
                    if alias not in existing_domains_list:
                        forge_api.create_site_domain(server_id, site_id, alias)
                        logger.info(f"Domain '{alias}' added to site.")

                logger.info("Site aliases configured successfully.")

        except Exception as e:
            raise Exception("Error updating aliases.") from e

        # ---- nginx custom config ----

        try:
            if site_conf.get("nginx_custom_config"):
                nginx_custom_file_path = cat_paths(
                    SOURCE_REPO_PATH, site_conf.get("nginx_custom_config")
                )
                with open(nginx_custom_file_path, "r") as file:
                    nginx_custom_content = file.read()

                logger.debug(
                    f"Nginx custom config file content:\n{nginx_custom_content}"
                )
                # compare existing site nginx config and the one in the file if different update
                site_existing_nginx_config = forge_api.get_nginx_config(
                    server_id, site_id
                )["attributes"]["content"]
                if site_existing_nginx_config != nginx_custom_content:
                    forge_api.set_nginx_config(server_id, site_id, nginx_custom_content)
                    logger.info(f"Nginx config updated.")
        except FileNotFoundError as e:
            raise Exception(
                f"Nginx config file `{site_conf.get('nginx_custom_config')} doesn't exist."
            ) from e
        except Exception as e:
            raise Exception("Error when trying to set custom nginx config") from e

        # ---- php version ----

        try:
            site_php_version = (
                forge_api.get_site_by_id(server_id, site_id)["attributes"][
                    "php_version"
                ]
                .replace("PHP ", "php")
                .replace(".", "")
            )

        except Exception as e:
            raise Exception("Failed to get site php version") from e

        if (
            site_conf.get("php_version")
            and site_conf.get("php_version") != site_php_version
        ):
            # update site php version
            logger.debug(
                f"php version changed from {site_php_version} to {site_conf.get('php_version')}, updating..."
            )
            forge_api.update_site(
                server_id, site_id, php_version=site_conf.get("php_version")
            )
            logger.info(f"Php version set to {site_conf.get('php_version')}")

        site_user = site_conf.get("isolated_user") if site_conf["isolated"] else "forge"
        site_dir = cat_paths(
            f"/home/{site_user}/",
            site_conf["domain_name"],
            "current" if site_conf["zero_downtime_deployments"] else ".",
            site_conf["root_dir"],
        )

        # create daemons
        try:
            daemon_ids = []
            # get existing site daemons
            server_daemons = forge_api.get_server_daemons(server_id)
            # existing site daemons
            site_daemons = [
                daemon
                for daemon in server_daemons
                if daemon["attributes"]["directory"] == site_dir
            ]
            # delete daemon if not in the config
            for dm in site_daemons:
                if dm["attributes"]["command"] not in [
                    daemon["command"] for daemon in site_conf["processes"]
                ]:
                    forge_api.delete_daemon(server_id, dm["id"])
                    logger.info(
                        f"Daemon-{dm['id']} `{dm["attributes"]['command']}` deleted."
                    )
                else:
                    daemon_ids.append(dm["id"])

            # add new daemons
            for process in site_conf["processes"]:
                if process["command"] not in [
                    dm["attributes"]["command"] for dm in site_daemons
                ]:
                    new_daemon = forge_api.create_daemon(
                        server_id,
                        process["name"],
                        process["command"],
                        site_dir,
                        user=site_user,
                    )
                    daemon_ids.append(new_daemon["id"])
                    logger.info(
                        f"Daemon-{new_daemon['id']} `{new_daemon['attributes']['command']}` created."
                    )
        except Exception as e:
            raise Exception(f"Failed to add daemons: {e}") from e

        # ----------Scheduler----------
        if site_conf["project_type"] == "laravel":
            try:
                scheduler_php_version = (
                    forge_api.get_site_by_id(server_id, site_id)["attributes"][
                        "php_version"
                    ]
                    .replace("PHP", "php")
                    .replace(" ", "")
                )

                scheduler_cmd = (
                    f"{scheduler_php_version} {site_dir}/artisan schedule:run"
                )

                server_jobs = forge_api.get_server_jobs(server_id)
                current_scheduler_job = next(
                    (
                        job
                        for job in server_jobs
                        if job["attributes"]["command"] == scheduler_cmd
                    ),
                    None,
                )

                if site_conf["laravel_scheduler"] and not current_scheduler_job:
                    forge_api.create_job(server_id, scheduler_cmd, "minutely")
                    logger.info("Scheduler job created successfully")
                elif not site_conf["laravel_scheduler"] and current_scheduler_job:
                    forge_api.delete_job(server_id, current_scheduler_job["id"])
                    logger.info("Scheduler job deleted successfully")

            except Exception as e:
                raise Exception(f"Failed to configure laravel scheduler: {e}") from e

        # deployment script
        # if deployment_script not provided, the default deployment script generated by forge is kept
        if site_conf.get("deployment_script"):
            deployment_script = f"# Generated by deployment action, do not modify\n"

            if not site_conf["zero_downtime_deployments"]:
                deployment_script += (
                    f"cd {site_dir}\n"
                    + "git fetch --prune --tags origin\n"
                    + 'git reset --hard "origin/$FORGE_SITE_BRANCH"\n'
                )
            else:
                deployment_script += (
                    "$CREATE_RELEASE()\n"
                    + "cd $FORGE_RELEASE_DIRECTORY\n"
                    + (
                        f"cd {site_conf["root_dir"]}\n"
                        if site_conf["root_dir"] != "."
                        else ""
                    )
                )

            deployment_script += site_conf.get("deployment_script") + "\n"

            if site_conf["zero_downtime_deployments"]:
                deployment_script += "$ACTIVATE_RELEASE()\n"

            for d_id in daemon_ids:
                deployment_script += f"sudo supervisorctl restart daemon-{d_id}:*\n"

            try:
                forge_api.update_deployment_script(
                    server_id,
                    site_id,
                    deployment_script,
                    auto_source=False,
                )
            except Exception as e:
                raise Exception(f"Failed to add deployment script: {e}") from e

            logger.info("Deployment script added successfully")

        # set env
        try:
            site_env = {}
            # read env file
            if site_conf.get("env_file"):
                env_file_path = cat_paths(SOURCE_REPO_PATH, site_conf.get("env_file"))
                try:
                    with open(env_file_path, "r") as file:
                        logger.info(
                            "Loading environment variables from file `%s`",
                            site_conf.get("env_file"),
                        )
                        env_file_content = file.read()
                        logger.debug("Env file content:\n%s", env_file_content)
                        # replace screts
                        env_file_content = str(
                            replace_secrets_and_envs_yaml(env_file_content, secrets)
                        )
                        # parse env
                        file_env = parse_env(env_file_content)
                        site_env.update(file_env)
                except FileNotFoundError as e:
                    raise Exception(
                        f"Environment file `{site_conf.get('env_file')}` not found"
                    ) from e

            if site_conf.get("environment"):
                config_env = parse_env(site_conf.get("environment"))
                site_env.update(config_env)

            env_str = "\n".join([f"{k}={v}" for k, v in site_env.items()])
            if len(env_str) > 0:
                forge_api.update_site_environment(server_id, site_id, env_str)
                logger.info("Environment variables set successfully")

        except Exception as e:
            raise Exception(f"Failed to set environment variables: {e}") from e

        # certificate
        try:
            if site_conf["certificate"]:
                # Get all site domains
                all_domains = forge_api.get_site_domains(server_id, site_id)

                # Filter out on-forge.com domains
                domains_to_certify = [
                    domain
                    for domain in all_domains
                    if not domain["attributes"]["name"].endswith(".on-forge.com")
                ]

                # For each domain, check if certificate exists and create if needed
                for domain in domains_to_certify:
                    domain_id = domain["id"]
                    domain_name = domain["attributes"]["name"]

                    # Check if domain has a certificate
                    if not forge_api.domain_has_certificate(
                        server_id, site_id, domain_id
                    ):
                        logger.info(
                            f"Installing certificate for domain '{domain_name}'..."
                        )

                        # Create certificate
                        cert = forge_api.create_domain_certificate(
                            server_id, site_id, domain_id
                        )

                        # Wait for certificate to be installed
                        def until_cert_installed():
                            domain_cert = forge_api.get_domain_certificate(
                                server_id, site_id, domain_id
                            )
                            if not domain_cert:
                                return True  # certificate failed
                            return domain_cert["attributes"]["status"] == "installed"

                        if not wait(until_cert_installed):
                            raise Exception(
                                f"Certificate installation timed out for domain '{domain_name}'"
                            )

                        cert = forge_api.get_domain_certificate(
                            server_id, site_id, domain_id
                        )
                        if cert:
                            logger.info(
                                f"Certificate installed for domain '{domain_name}'"
                            )
                        else:
                            raise Exception(
                                f"Certificate installation failed for domain '{domain_name}'"
                            )
                    else:
                        logger.info(
                            f"Certificate already exists for domain '{domain_name}'"
                        )

        except Exception as e:
            raise Exception(f"Failed to manage certificates: {e}") from e

        # deploy site
        if site_conf["clone_repository"]:
            logger.info("Deploying site...")

            # Trigger deployment and get deployment ID
            deployment_id = forge_api.deploy_site(server_id, site_id)["id"]
            logger.debug(f"Deployment ID: {deployment_id}")

            # Wait until deployment is finished
            def until_deployment_finished():
                status_data = forge_api.get_deployment(
                    server_id, site_id, deployment_id
                )
                status = status_data["attributes"]["status"]
                logger.debug(f"Deployment status: {status}")

                # Check for failed states
                if status in ["cancelled", "failed", "failed-build"]:
                    return True

                # Check for success
                if status == "finished":
                    return True

                # Still in progress
                return False

            if not wait(until_deployment_finished, max_retries=-1):
                raise Exception("Deployment status check timed out")

            # Get final status
            final_status_data = forge_api.get_deployment(
                server_id, site_id, deployment_id
            )
            final_status = final_status_data["attributes"]["status"]

            # Get deployment log (always show it)
            deployment_log = forge_api.get_deployment_log(
                server_id, site_id, deployment_id
            )["attributes"]["output"]
            if deployment_log:
                logger.info("Deployment log:\n%s", deployment_log)
            else:
                logger.warning("Deployment log not available")

            # Check if deployment failed
            if final_status in ["cancelled", "failed", "failed-build"]:
                raise Exception(f"Deployment failed with status: {final_status}")

            logger.info("Site deployed successfully")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err, exc_info=True)
        sys.exit(1)
    except Exception as err:
        logger.error("An error occurred:\n %s", err, exc_info=True)
        sys.exit(1)
