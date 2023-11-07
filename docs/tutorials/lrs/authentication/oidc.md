# OpenID Connect authentication

Ralph LRS also supports OpenID Connect on top of OAuth 2.0 for authentication and authorization.

To enable OpenID Connect authentication mode, we should change the `RALPH_RUNSERVER_AUTH_BACKENDS` environment variable to `oidc` and we should define the `RALPH_RUNSERVER_AUTH_OIDC_ISSUER_URI` environment variable with the identity provider's Issuer Identifier URI as follows:

```bash
RALPH_RUNSERVER_AUTH_BACKENDS=oidc
RALPH_RUNSERVER_AUTH_OIDC_ISSUER_URI=http://{provider_host}:{provider_port}/auth/realms/{realm_name}
```

This address must be accessible to the LRS on startup as it will perform OpenID Connect Discovery to retrieve public keys and other information about the OpenID Connect environment.

It is also strongly recommended to set the optional `RALPH_RUNSERVER_AUTH_OIDC_AUDIENCE` environment variable to the origin address of Ralph LRS itself (e.g. "http://localhost:8100") to enable verification that a given token was issued specifically for that Ralph LRS.

## Identity Providers

OpenID Connect support is currently developed and tested against [Keycloak](https://www.keycloak.org/) but may work with other identity providers that implement the specification.

## An example with Keycloak

The [Learning analytics playground](https://github.com/openfun/learning-analytics-playground/) repository contains a Docker Compose file and configuration for a demonstration instance of Keycloak with a `ralph` client.

First, we should stop the Ralph LRS server (if it's still running):
```bash
docker compose down
```

We can clone the `learning-analytics-playground` repository:
```bash
git clone git@github.com:openfun/learning-analytics-playground
```

And then bootstrap the project:
```bash
cd learning-analytics-playground/
make bootstrap
```

After a couple of minutes, the playground containers should be up and running.



Create another docker compose file, let's call it `docker-compose.oidc.yml`, with the following content:
```yaml title="docker-compose.oidc.yml" hl_lines="9-10 26-27 29-31"
version: "3.9"

services:

  lrs:
    image: fundocker/ralph:latest
    environment:
      RALPH_APP_DIR: /app/.ralph
      RALPH_RUNSERVER_AUTH_BACKENDS: oidc
      RALPH_RUNSERVER_AUTH_OIDC_ISSUER_URI: http://learning-analytics-playground-keycloak-1:8080/auth/realms/fun-mooc
      RALPH_RUNSERVER_BACKEND: fs
    ports:
      - "8100:8100"
    command:
      - "uvicorn"
      - "ralph.api:app"
      - "--proxy-headers"
      - "--workers"
      - "1"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8100"
    volumes:
      - .ralph:/app/.ralph
    networks:
      - ralph

networks:
  ralph:
    external: true
    
```

Again, we need to create the `.ralph` directory:
```bash
mkdir .ralph
```

Then we can start the `lrs` service:
```bash
docker compose -f docker-compose.oidc.yml up -d lrs
```

Now that both Keycloak and Ralph LRS server are up and running, we should be able to get the access token from Keycloak with the command:

=== "curl"

    ```bash
    curl -X POST \
      -d "grant_type=password" \
      -d "client_id=ralph" \
      -d "client_secret=bcef3562-730d-4575-9e39-63e185f99bca" \
      -d "username=ralph_admin" \
      -d "password=funfunfun" \
      http://localhost:8080/auth/realms/fun-mooc/protocol/openid-connect/token
    ```

    ```bash
    {"access_token":"<access token content>","expires_in":300,"refresh_expires_in":1800,"refresh_token":"<refresh token content>","token_type":"Bearer","not-before-policy":0,"session_state":"0889b3a5-d742-45fb-98b3-20e967960e74","scope":"email profile"} 
    ```
=== "HTTPie"

    ```bash
    http -f POST \
      :8080/auth/realms/fun-mooc/protocol/openid-connect/token \
      grant_type=password \
      client_id=ralph \
      client_secret=bcef3562-730d-4575-9e39-63e185f99bca \
      username=ralph_admin \
      password=funfunfun
    ```

    ```bash
    HTTP/1.1 200 OK
    ...
    {
        "access_token": "<access token content>",
        "expires_in": 300,
        "not-before-policy": 0,
        "refresh_expires_in": 1800,
        "refresh_token": "<refresh token content>",
        "scope": "email profile",
        "session_state": "1e826fa2-b4b3-42bf-837f-158fe9d5e1e5",
        "token_type": "Bearer"
    }
    ```

With this access token, we can now make a request to the Ralph LRS server:

=== "curl"
    
    ```bash
    curl -H 'Authorization: Bearer <access token content>' \
    http://localhost:8100/whoami
    ```
    
    ```bash
    {"agent":{"openid":"http://localhost:8080/auth/realms/fun-mooc/b6e85bd0-ce6e-4b24-9f0e-6e18d8744e54"},"scopes":["email","profile"]}
    ```

=== "HTTPie"

    ```bash
    http -A bearer -a <access token content> :8100/whoami
    ```

    ```bash
    HTTP/1.1 200 OK
    ...
    {
        "agent": {
            "openid": "http://localhost:8080/auth/realms/fun-mooc/b6e85bd0-ce6e-4b24-9f0e-6e18d8744e54"
        },
        "scopes": [
            "email",
            "profile"
        ]
    }
    ```

Congrats, you've managed to authenticate using OpenID Connect! 🎉
