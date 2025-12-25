from typing import Literal

import requests

from utils import format_php_version


class ForgeApi:
    def __init__(self, api_token, org):
        self.forge_uri = f"https://forge.laravel.com/api/orgs/{org}"

        self.session = requests.sessions.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # --- Servers ---
    def get_server_by_name(self, server_name):
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers?filter[name]={server_name}"
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to get server from Laravel Forge API") from e
        servers = response.json()["data"]

        # Filter returns substring matches, so find exact match
        exact_matches = [s for s in servers if s["attributes"]["name"] == server_name]

        if len(exact_matches) == 0:
            raise Exception(f"Server '{server_name}' not found in Laravel Forge")

        return exact_matches[0]

    # --- Sites ---
    def create_site(self, server_id, payload):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/sites",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["data"]

        except requests.RequestException as e:
            raise Exception("Failed to create site from Laravel Forge API") from e

    def get_all_sites(self, server_id):
        try:
            response = self.session.get(f"{self.forge_uri}/servers/{server_id}/sites")
            response.raise_for_status()
            sites = response.json()["data"]
            return sites
        except requests.RequestException as e:
            raise Exception("Failed to get sites from Laravel Forge API") from e

    def get_site_by_id(self, server_id, site_id):
        try:
            res = self.session.get(f"{self.forge_uri}/sites/{site_id}")
            res.raise_for_status()
            return res.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to get site from Laravel Forge API") from e

    def update_site(self, server_id, site_id, **kwargs):
        try:
            response = self.session.put(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}",
                json={**kwargs},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to update site from Laravel Forge API") from e

    def update_deployment_script(self, server_id, site_id, content, auto_source=False):
        try:
            response = self.session.put(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/deployments/script",
                json={
                    "content": content,
                    "auto_source": auto_source,
                },
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to update deployment script from Laravel Forge API"
            ) from e

    def update_site_environment(self, server_id, site_id, content):
        try:
            response = self.session.put(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/environment",
                json={
                    "environment": content,
                },
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(
                "Failed to update site environment from Laravel Forge API"
            ) from e

    def deploy_site(self, server_id, site_id):
        """Trigger a site deployment. Returns the deployment ID."""
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/deployments"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to deploy site from Laravel Forge API") from e

    def get_deployment(self, server_id, site_id, deployment_id):
        """Get the status of a deployment."""
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/deployments/{deployment_id}"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to get deployment status from Laravel Forge API"
            ) from e

    def get_deployment_log(self, server_id, site_id, deployment_id):
        """Get the deployment log. Returns None if log doesn't exist (404)."""
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/deployments/{deployment_id}/log"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                return None
            raise Exception(
                "Failed to get deployment log from Laravel Forge API"
            ) from e

    # --- nginx ---

    def get_nginx_templates_by_name(self, server_id, name) -> dict | None:
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/nginx/templates?filter[name]={name}"
            )
            response.raise_for_status()
            templates = response.json()["data"]

            # Filter returns substring matches, so find exact match
            exact_matches = [t for t in templates if t["attributes"]["name"] == name]

            if len(exact_matches) == 0:
                return None

            return exact_matches[0]
        except requests.RequestException as e:
            raise Exception(
                "Failed to get nginx templates from Laravel Forge API"
            ) from e

    def create_nginx_template(self, server_id, name, content):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/nginx/templates",
                json={
                    "content": content,
                    "name": name,
                },
            )
            response.raise_for_status()
            return response.json()["data"]["id"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to create nginx template from Laravel Forge API"
            ) from e

    def get_nginx_config(self, server_id, site_id):
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/nginx"
            )
            response.raise_for_status()
            return response.json()["data"]

        except requests.RequestException as e:
            raise Exception("Failed to get nginx config from Laravel Forge API") from e

    def set_nginx_config(self, server_id, site_id, nginx_config):
        try:
            response = self.session.put(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/nginx",
                json={"config": nginx_config},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to set nginx config from Laravel Forge API") from e

    # --- Domains ---
    def get_site_domains(self, server_id, site_id):
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to get site domains from Laravel Forge API") from e

    def create_site_domain(self, server_id, site_id, domain):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains",
                json={
                    "name": domain,
                    "allow_wildcard_subdomains": False,
                    "www_redirect_type": "none",
                },
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to create site domain from Laravel Forge API"
            ) from e

    def delete_site_domain(self, server_id, site_id, domain_id):
        try:
            response = self.session.delete(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains/{domain_id}"
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(
                "Failed to delete site domain from Laravel Forge API"
            ) from e

    def domain_has_certificate(self, server_id, site_id, domain_id):
        """Check if a domain has a certificate. Returns True if certificate exists, False otherwise."""
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains/{domain_id}/certificate"
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                return False
            raise Exception(
                "Failed to check domain certificate from Laravel Forge API"
            ) from e

    def get_domain_certificate(self, server_id, site_id, domain_id):
        """Get the certificate for a specific domain. Returns None if not found."""
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains/{domain_id}/certificate"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                return None
            raise Exception(
                "Failed to get domain certificate from Laravel Forge API"
            ) from e

    def create_domain_certificate(self, server_id, site_id, domain_id):
        """Create a LetsEncrypt certificate for a domain."""
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/sites/{site_id}/domains/{domain_id}/certificate",
                json={
                    "type": "letsencrypt",
                    "letsencrypt": {
                        "verification_method": "http-01",
                        "key_type": "ecdsa",
                    },
                },
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to create domain certificate from Laravel Forge API"
            ) from e

    # --- Php ---

    def get_server_installed_php_versions(self, server_id):
        try:
            res = self.session.get(f"{self.forge_uri}/servers/{server_id}/php/versions")
            res.raise_for_status()
            return res.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to get installed PHP versions") from e

    def get_php_version(self, server_id, version):
        """Get a specific PHP version by filtering. Returns None if not found."""
        try:
            res = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/php/versions?filter[version]={version}"
            )
            res.raise_for_status()
            versions = res.json()["data"]
            return versions[0] if len(versions) > 0 else None
        except requests.RequestException as e:
            raise Exception("Failed to get PHP version") from e

    def install_php_version(self, server_id, version):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/php/versions",
                json={"version": version},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to install PHP version") from e

    # --- Daemons ---
    def get_server_daemons(self, server_id):
        try:
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/background-processes"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception(
                "Failed to get server daemons from Laravel Forge API"
            ) from e

    def create_daemon(self, server_id, name, command, directory, user="forge"):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/background-processes",
                json={
                    "name": name,
                    "command": command,
                    "user": user,
                    "directory": directory,
                    "processes": 1,
                },
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to create daemon from Laravel Forge API") from e

    def delete_daemon(self, server_id, daemon_id):
        try:
            response = self.session.delete(
                f"{self.forge_uri}/servers/{server_id}/background-processes/{daemon_id}"
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to delete daemon from Laravel Forge API") from e

    # --- Cron Jobs ---
    def get_server_jobs(self, server_id):
        try:
            # get current schedule job
            response = self.session.get(
                f"{self.forge_uri}/servers/{server_id}/scheduled-jobs"
            )
            response.raise_for_status()
            return response.json()["data"]
        except requests.RequestException as e:
            raise Exception("Failed to get server jobs from Laravel Forge API") from e

    def create_job(
        self,
        server_id,
        cmd: str,
        frequency: Literal["minutely", "hourly", "nightly", "weekly", "monthly"],
        user="forge",
    ):
        try:
            response = self.session.post(
                f"{self.forge_uri}/servers/{server_id}/scheduled-jobs",
                json={
                    "user": user,
                    "command": cmd,
                    "frequency": frequency,
                },
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to create job from Laravel Forge API") from e

    def delete_job(self, server_id, job_id):
        try:
            response = self.session.delete(
                f"{self.forge_uri}/servers/{server_id}/scheduled-jobs/{job_id}"
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Failed to delete job from Laravel Forge API") from e
