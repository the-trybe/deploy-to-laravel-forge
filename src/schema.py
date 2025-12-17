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
                "www_redirect_type": {
                    "type": "string",
                    "required": False,
                    "default": "none",
                    "allowed": ["from-www", "to-www", "none"],
                },
                "github_branch": {
                    "type": "string",
                    "required": False,
                },
                "root_dir": {
                    "type": "string",
                    "required": False,
                    "default": ".",
                    "coerce": "relative_path",
                },
                "web_dir": {
                    "type": "string",
                    "required": False,
                    "default": "public",
                    "coerce": "relative_path",
                },
                "project_type": {
                    "type": "string",
                    "required": False,
                    "default": "laravel",
                    "allowed": [
                        "laravel",
                        "other",
                    ],
                },
                "php_version": {"type": "string", "required": False},  # ex php84
                "install_composer_dependencies": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                "deployment_script": {
                    "type": "string",
                    "required": False,
                },
                "processes": {
                    "type": "list",
                    "required": False,
                    "default": [],
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "name": {"type": "string", "required": True},
                            "command": {"type": "string", "required": True},
                        },
                    },
                },
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
                "isolated": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "isolated_user_required": True,
                },
                "isolated_user": {
                    "type": "string",
                    "required": False,
                },
                "zero_downtime_deployments": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                "shared_paths": {
                    "type": "list",
                    "required": False,
                    "default": [],
                    "schema": {
                        "anyof": [
                            {"type": "string"},
                            {
                                "type": "dict",
                                "schema": {
                                    "from": {"type": "string", "required": True},
                                    "to": {"type": "string", "required": True},
                                },
                            },
                        ]
                    },
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
