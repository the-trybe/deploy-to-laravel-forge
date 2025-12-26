# Deploy to Laravel Forge GitHub Action

A GitHub Action that automates site provisioning, configuration, and deployment on Laravel Forge using a declarative YAML configuration file.

## Quick Start

Create a workflow file at `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Forge

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: the-trybe/deploy-to-laravel-forge@v2
        with:
          forge_api_token: ${{ secrets.FORGE_API_TOKEN }}
          secrets: |
            APP_KEY=${{ secrets.APP_KEY }}
```

Create a `forge-deploy.yml` file in your repository root:

```yaml
organization: "your-forge-organization"
server: "production-server"
github_repository: "username/repository"
github_branch: "main"

sites:
  - name: "example"
    domain_mode: "on-forge" # Creates example.on-forge.com
    project_type: "laravel"
    php_version: "php84"
    deployment_script: |
      composer install --no-dev
      php artisan migrate --force
    environment: |
      APP_ENV=production
      APP_KEY=${{ secrets.APP_KEY }}
```

## Examples

Some configuration examples are available in the [`examples/`](examples/) directory.

## Configuration Reference

### Action Inputs

| Input             | Required | Default            | Description                                              |
| ----------------- | -------- | ------------------ | -------------------------------------------------------- |
| `forge_api_token` | Yes      | -                  | Laravel Forge API token                                  |
| `deployment_file` | No       | `forge-deploy.yml` | Path to deployment configuration file                    |
| `secrets`         | No       | -                  | Secret values to replace in config (format: `KEY=value`) |
| `debug`           | No       | `false`            | Enable verbose logging                                   |

### Deployment File Schema

```yaml
# Required: Forge organization name
organization: "string"

# Required: Forge server name
server: "string"

# Required: GitHub repository (format: owner/repo)
github_repository: "string"

# Optional: Default branch to deploy (default: "main")
github_branch: "string"

# Required: List of sites to configure
sites:
  - # Required: Site identifier (used to construct domain)
    name: "string"

    # Optional: Domain mode (default: "on-forge")
    # "on-forge": Creates {name}.on-forge.com
    # "custom": Uses {name} as the full domain
    domain_mode: "on-forge|custom"

    # Optional: WWW redirect behavior (default: "none")
    # "from-www": Redirects www.domain to domain
    # "to-www": Redirects domain to www.domain
    # "none": No redirect
    www_redirect_type: "from-www|to-www|none"

    # Optional: Branch override for this site (default: uses global github_branch)
    github_branch: "string"

    # Optional: Directory containing the application root (default: ".")
    root_dir: "string"

    # Optional: Public web directory relative to root_dir (default: "public")
    web_dir: "string"

    # Optional: Project type (default: "laravel")
    project_type: "laravel|other"

    # Optional: PHP version (e.g., "php81", "php82", "php83", "php84")
    # Installs version if not present on server
    php_version: "string"

    # Optional: Install Composer dependencies during site creation (default: false)
    install_composer_dependencies: boolean

    # Optional: Custom deployment script
    # If omitted, uses Forge's default deployment script
    deployment_script: |
      # Your deployment commands
      composer install --no-dev
      php artisan migrate --force

    # Optional: Background processes to run (default: [])
    processes:
      - name: "string" # Process name
        command: "string" # Command to execute

    # Optional: Enable Laravel scheduler (default: false)
    # Creates cron job: {php_version} {root_dir}/artisan schedule:run
    laravel_scheduler: boolean

    # Optional: Environment variables from inline string
    environment: |
      KEY=value
      ANOTHER_KEY=${{ secrets.SECRET_VAR }}

    # Optional: Environment variables from file
    # File path relative to repository root
    # If both env_file and environment are set, environment takes precedence
    env_file: "string"

    # Optional: Additional domain aliases (default: [])
    aliases:
      - "www.example.com"
      - "alias.example.com"

    # Optional: Nginx template name from nginx_templates/ folder
    # Built-in templates: reverse-proxy
    nginx_template: "string"

    # Optional: Variables to replace in nginx template (default: {})
    # Use {{ VARIABLE_NAME }} in template file
    nginx_template_variables:
      KEY: "value"

    # Optional: Path to custom nginx configuration file
    # File path relative to repository root
    # Overrides template if both are specified
    nginx_custom_config: "string"

    # Optional: Create SSL certificate for all non-.on-forge.com domains (default: false)
    certificate: boolean

    # Optional: Run site as isolated user (default: false)
    isolated: boolean

    # Optional: Isolated user name (required if isolated: true)
    isolated_user: "string"

    # Optional: Enable zero-downtime deployments (default: false)
    zero_downtime_deployments: boolean

    # Optional: Shared paths for zero-downtime deployments (default: [])
    # Paths can be strings or objects with "from" and "to" keys
    shared_paths:
      - "storage" # Simple: links same path in shared and release
      - from: "storage" # Explicit: custom source and destination
        to: "public/storage"

    # Optional: Clone repository during site creation (default: true)
    # Set to false for manually deployed sites
    clone_repository: boolean
```

## Detailed Guides

### Secret Management

Secrets can be injected using `${{ secrets.NAME }}` or `${{ env.NAME }}` syntax in the deployment file.

**Using GitHub Secrets:**

```yaml
# .github/workflows/deploy.yml
- uses: the-trybe/deploy-to-laravel-forge@v2
  with:
    forge_api_token: ${{ secrets.FORGE_API_TOKEN }}
    secrets: |
      DB_PASSWORD=${{ secrets.DB_PASSWORD }}
      API_KEY=${{ secrets.API_KEY }}
```

```yaml
# forge-deploy.yml
environment: |
  DB_PASSWORD=${{ secrets.DB_PASSWORD }}
  API_KEY=${{ secrets.API_KEY }}
```

**Using Environment Variables:**

```yaml
# .github/workflows/deploy.yml
- name: Set environment variables
  run: |
    echo "APP_NAME=my-app-name" >> $GITHUB_ENV
    echo "APP_DOMAIN=my-app-domain" >> $GITHUB_ENV

- uses: the-trybe/deploy-to-laravel-forge@v2
  with:
    forge_api_token: ${{ secrets.FORGE_API_TOKEN }}
```

```yaml
# forge-deploy.yml
environment: |
  APP_NAME=${{ env.APP_NAME }}
  APP_DOMAIN=${{ env.APP_DOMAIN }}
```

**Using HashiCorp Vault:**

```yaml
# .github/workflows/deploy.yml
- uses: hashicorp/vault-action@v2
  with:
    url: https://vault.example.com
    path: jwt-github-actions
    role: your-jwt-role
    method: jwt
    secrets: |
      secrets/data/your-project/production/env *

- uses: the-trybe/deploy-to-laravel-forge@v2
  with:
    forge_api_token: ${{ env.FORGE_API_TOKEN }}
    deployment_file: forge-deploy.yml
```

See the [HashiCorp Vault Action documentation](https://github.com/hashicorp/vault-action) for configuration details.

### Nginx Templates

Nginx templates are loaded in the following order:

1. **Existing server templates**: Templates already created in your Forge server
2. **Built-in community templates**: Templates from the `nginx_templates/` directory of this action (used if not found on server)

The action includes community-contributed templates that can be used directly. Current built-in templates:

- `reverse-proxy`: Basic reverse proxy configuration for Node.js, Go, or other HTTP services

#### Using Templates

Templates support variable substitution using `{{ VARIABLE_NAME }}` syntax.

**Example configuration:**

```yaml
nginx_template: "reverse-proxy"
nginx_template_variables:
  PROXY_PORT: "3000"
```

**Example template content:**

```nginx
location / {
    proxy_pass http://127.0.0.1:{{ PROXY_PORT }};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

#### Adding Custom Templates

To use a custom template not available on your server:

1. Add your template file to the `nginx_templates/` directory in a fork of this action
2. Reference it by filename (without `.conf` extension) in your deployment file

**Important:** Avoid using [Forge reserved variables](https://forge.laravel.com/docs/servers/nginx-templates.html#template-variables) in custom templates.

### Zero-Downtime Deployments

Enable zero-downtime deployments to minimize service interruption during updates. Forge creates a new release directory for each deployment and symlinks it to `current` after successful completion.

**Configuration:**

```yaml
zero_downtime_deployments: true
shared_paths:
  - "storage"
  - "bootstrap/cache"
  - from: ".env"
    to: ".env"
```

**Important:** The `deployment_script` must not include repository cloning commands when zero-downtime is enabled. The action automatically wraps your script with `$CREATE_RELEASE()` and `$ACTIVATE_RELEASE()` commands.

### PHP Version Management

The action automatically installs PHP versions that don't exist on the server. Version format: `php` + major + minor (e.g., `php81`, `php82`, `php84`).

```yaml
php_version: "php84"
```

The action waits for installation to complete before proceeding with site creation.

### Isolated Sites

Isolated sites run under a dedicated system user instead of the shared `forge` user. This provides process and filesystem isolation between sites.

```yaml
isolated: true
isolated_user: "myappuser"
```

The `isolated_user` is required when `isolated` is set to `true`.

### Background Processes

Processes are managed by Supervisor. The action automatically restarts processes after deployment when a `deployment_script` is provided.

```yaml
processes:
  - name: "queue-worker"
    command: "php artisan queue:work --tries=3"
  - name: "websocket-server"
    command: "php artisan websockets:serve"
```

### Multiple Sites

Deploy multiple sites to the same server by adding entries to the `sites` array. Each site is configured independently and can use different branches, PHP versions, and configurations.

```yaml
sites:
  - name: "production"
    github_branch: "main"
    php_version: "php84"

  - name: "staging"
    github_branch: "develop"
    php_version: "php83"
```
