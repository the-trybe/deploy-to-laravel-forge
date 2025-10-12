schema = {
    "organization": {"type": "string", "required": True},
    "server": {"type": "string", "required": True},
    "github_repository": {"type": "string", "required": True},
    "github_branch": {"type": "string", "required": False, "default": "main"},
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "domain_mode": {
                    "type": "string",
                    "required": False,
                    "default": "on-forge",
                    "allowed": [
                        "on-forge",
                        "custom",
                    ],
                },
                "name": {"type": "string", "required": True},
                "github_branch": {
                    "type": "string",
                    "required": False,
                },
                "root_dir": {"type": "string", "required": False, "default": "."},
                "web_dir": {
                    "type": "string",
                    "required": False,
                    "default": "public",
                },
                "project_type": {
                    "type": "string",
                    "required": False,
                    "default": "other",
                    "allowed": [
                        "laravel",
                        "symfony",
                        "statamic",
                        "wordpress",
                        "phpmyadmin",
                        "php",
                        "next.js",
                        "nuxt.js",
                        "static-html",
                        "other",
                    ],
                },
                "php_version": {"type": "string", "required": False},
                "deployment_commands": {
                    "type": "string",
                    "required": False,
                },
                "daemons": {"type": "list", "required": False, "default": []},
                "laravel_scheduler": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                "environment": {"type": "string", "required": False},
                "env_file": {"type": "string", "required": False},
                "aliases": {"type": "list", "required": False, "default": []},
                "nginx_template": {
                    "type": "string",
                    "required": False,
                    "default": "default",
                },
                "nginx_template_variables": {
                    "type": "dict",
                    "required": False,
                    "default": {},
                },
                "nginx_custom_config": {
                    "type": "string",
                    "required": False,
                },
                "certificate": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                "website_isolation": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "isolation_user_required": True,
                },
                "isolation_user": {
                    "type": "string",
                    "required": False,
                },
                "clone_repository": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                },
            },
        },
        "required": False,
        "default": [],
    },
}
