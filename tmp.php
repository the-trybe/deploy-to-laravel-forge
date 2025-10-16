<?php

$curl = curl_init();

curl_setopt_array($curl, [
  CURLOPT_URL => "https://forge.laravel.com/api/orgs/{organization}/servers/{server}/sites",
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => "",
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 30,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => "POST",
  CURLOPT_POSTFIELDS => json_encode([
    'type' => 'laravel',
    'domain_mode' => '<string>',
    'name' => '<string>',
    'www_redirect_type' => '<string>',
    'allow_wildcard_subdomains' => '<string>',
    'web_directory' => '<string>',
    'is_isolated' => null,
    'isolated_user' => '<string>',
    'php_version' => 'php5',
    'zero_downtime_deployments' => null,
    'nginx_template_id' => 123,
    'source_control_provider' => 'github',
    'repository' => '<string>',
    'branch' => '<string>',
    'database_id' => 123,
    'database_user_id' => '<string>',
    'statamic_setup' => '<string>',
    'statamic_starter_kit' => '<string>',
    'statamic_super_user_email' => '<string>',
    'statamic_super_user_password' => '<string>',
    'install_composer_dependencies' => null,
    'generate_deploy_key' => null,
    'public_deploy_key' => '<string>',
    'private_deploy_key' => '<string>',
    'nuxt_next_mode' => '<string>',
    'nuxt_next_build_command' => '<string>',
    'nuxt_next_port' => 123,
    'push_to_deploy' => null,
    'shared_paths' => [
      [
        'from' => '<string>',
        'to' => '<string>'
      ]
    ]
  ]),
  CURLOPT_HTTPHEADER => [
    "Authorization: Bearer <token>",
    "Content-Type: application/json"
  ],
]);

$response = curl_exec($curl);
$err = curl_error($curl);

curl_close($curl);

if ($err) {
  echo "cURL Error #:" . $err;
} else {
  echo $response;
}
