# First steps

Ralph LRS is distributed as a Docker image on [DockerHub](https://hub.docker.com/repository/docker/fundocker/ralph), following the format:
`fundocker/ralph:<release version | latest>`.

Let's dive straight in and create a `docker-compose.yml` file:

``` yaml title="docker-compose.yml"
version: "3.9"

services:

  lrs:
    image: fundocker/ralph:latest
    environment:
      RALPH_APP_DIR: /app/.ralph
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
```

For now, we are using the `fs` (File System) backend, meaning that Ralph LRS will store learning records in local files.

First, we need to manually create the `.ralph` directory alongside the `docker-compose.yml` file with the command:

```bash
mkdir .ralph
```

We can then run Ralph LRS from a terminal with the command:

```bash
docker compose up -d lrs
```

Ralph LRS server should be up and running!

We can request the `whoami` endpoint to check if the user is authenticated. On success, the endpoint returns the username and permission scopes.

=== "curl"

    ```bash
    curl http://localhost:8100/whoami
    ```
    ```console
    {"detail":"Invalid authentication credentials"}% 
    ```

=== "HTTPie"

    ```bash
    http :8100/whoami
    ```
    ```console
    HTTP/1.1 401 Unauthorized
    content-length: 47
    content-type: application/json
    date: Mon, 06 Nov 2023 15:37:32 GMT
    server: uvicorn
    www-authenticate: Basic

    {
        "detail": "Invalid authentication credentials"
    }

    ```

If you've made it this far, congrats! 🎉

You've successfully deployed the Ralph LRS and got a response to your request!

Let's shutdown the Ralph LRS server with the command `docker compose down` and set up authentication.
