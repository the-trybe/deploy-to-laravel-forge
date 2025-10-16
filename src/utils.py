import re
import time
from pathlib import Path

from schema import schema
from validator import ConfigValidator


def validate_yaml_data(data):
    v = ConfigValidator(schema, purge_unknown=True)  # type: ignore
    v.allow_default_values = True  # type: ignore
    if not v.validate(data, normalize=True):  # type: ignore
        raise Exception(f"YAML data validation failed: {v.errors}")  # type: ignore
    return v.document  # type: ignore


def replace_secrets_yaml(data, secrets):
    if isinstance(data, dict):
        return {
            key: replace_secrets_yaml(value, secrets) for key, value in data.items()
        }
    elif isinstance(data, list):
        return [replace_secrets_yaml(item, secrets) for item in data]
    elif isinstance(data, str):
        # regex matches all occurrences of secrets in the form ${{ secrets.SECRET_VAR }}
        pattern = re.compile(r"\$\{\{\s*secrets\.(\w+)\s*\}\}")

        def replace_match(match):
            secret_name = match.group(1).upper()
            if secret_name not in secrets:
                raise ValueError(f"Secret '{secret_name}' value is not set.")
            return secrets[secret_name]

        return pattern.sub(replace_match, data)
    else:
        return data


def replace_nginx_variables(nginx_conf, variables):
    pattern = re.compile(r"{{(.*?)}}")

    def replace_match(match):
        var_name = match.group(1).strip()

        try:
            var_value = variables[var_name]
        except KeyError:
            raise ValueError(f"Variable '{var_name}' value is not set.")

        return str(var_value)

    return pattern.sub(replace_match, nginx_conf)


def wait(callback, max_retries=8):
    retries = 0
    timeout = 0.5
    max_timeout = 30
    # max_retries < 0 means infinite retries
    while max_retries < 0 or retries <= max_retries:
        if callback():
            return True
        time.sleep(timeout)
        retries += 1
        timeout = min(timeout * 2, max_timeout)
    return False


def parse_env(env: str | None) -> dict[str, str]:
    if not env:
        return {}
    parsed_env = {}
    for line in env.strip().split("\n"):
        if line:
            try:
                key, value = line.split("=", 1)
                parsed_env[key.strip().upper()] = value.strip()
            except ValueError:
                print(
                    f"Error: Could not parse line: '{line}'. Make sure each line has a key and a value separated by '='."
                )
    return parsed_env


def cat_paths(*paths):
    return str(Path(*paths))


def ensure_relative_path(path: str | None):
    if path and path.startswith("/"):
        return "." + path
    return path


def get_domains_certificate(certificates, domains) -> dict | None:
    """Get the certificate for the given domains from the list of certificates."""
    for cert in certificates:
        cert_domains = cert["domain"].split(",")
        if set(cert_domains) == set(domains):
            return cert
    return None


def format_php_version(php_version: str) -> str:
    """
    Converts a PHP version string from the format 'php{major}{minor}' to 'php{major}.{minor}'.
    """
    match = re.match(r"php(\d)(\d+)", php_version)
    return f"php{match.group(1)}.{match.group(2)}" if match else "php"


def format_php_version_for_api(php_version: str) -> str:
    """
    Converts a PHP version string to the format expected by the Forge API.
    Handles formats like '8.4' or 'php8.4' and converts to 'php84'.
    """
    # Remove 'php' prefix if present
    version = php_version.lower().replace("php", "")
    # Remove dots
    version = version.replace(".", "")
    return f"php{version}"
