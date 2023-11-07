# HTTP Basic Authentication

The default method for securing the Ralph API server is HTTP Basic Authentication.
For this, we need to create a user in Ralph LRS.

## Creating user credentials

To create a new user credentials, Ralph CLI provides a dedicated command:

=== "Ralph CLI"

    ```bash
    ralph auth \
        --write-to-disk \
        --username janedoe \
        --password supersecret \
        --scope statements/write \
        --scope statements/read \
        --agent-ifi-mbox mailto:janedoe@example.com
    ```

=== "Docker Compose"
    
    ```bash
    docker compose run --rm lrs \
      ralph auth \
        --write-to-disk \
        --username janedoe \
        --password supersecret \
        --scope statements/write \
        --scope statements/read \
        --agent-ifi-mbox mailto:janedoe@example.com
    ```

!!! tip
    You can either display the helper with `ralph auth --help` or check the CLI tutorial [here](../../cli.md)

This command updates your credentials file with the new `janedoe` user.
Here is the file that has been created by the `ralph auth` command:

```json title="auth.json"
[                                                                               
  {                                                                             
    "agent": {                                                                  
      "mbox": "mailto:janedoe@example.com",                                     
      "objectType": "Agent",                                                    
      "name": null                                                              
    },                                                                          
    "scopes": [                                                                 
      "statements/write",                                                           
      "statements/read"
    ],                                                                          
    "hash": "$2b$12$eQmMF/7ALdNuksL4lkI.NuTibNjKLd0fw2Xe.FZqD0mNkgnnjLLPa",     
    "username": "janedoe"                                                       
  }                                                                             
] 
```

Alternatively, the credentials file **can also be created manually**. It is expected to be a valid JSON file. Its location is specified by the `RALPH_AUTH_FILE` configuration value. 

!!! tip
    By default, Ralph LRS looks for the `auth.json` file in the application directory (see [click
    documentation for
    details](https://click.palletsprojects.com/en/8.1.x/api/#click.get_app_dir)).

The expected format is a list of entries (JSON objects) each containing:

- the username
- the user's hashed+salted password
- the scopes they can access
- an `agent` object used to represent the user in the LRS. 

!!! info

    The `agent` is constrained by [LRS specifications](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#description-2), and must use one of four valid [Inverse Functional Identifiers](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#inversefunctional).


## Making a GET request

After changing the `docker-compose.yml` file as follow:
``` yaml hl_lines="10" title="docker-compose.yml"
version: "3.9"

services:

  lrs:
    image: fundocker/ralph:latest
    environment:
      RALPH_APP_DIR: /app/.ralph
      RALPH_RUNSERVER_BACKEND: fs
      RALPH_RUNSERVER_AUTH_BACKENDS: basic
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
and running the Ralph LRS with:

```bash
docker compose up -d lrs
```

we can request the `whoami` endpoint again, but this time sending our username and password through Basic Auth:

=== "curl"

    ```
    curl --user janedoe:supersecret http://localhost:8100/whoami
    ```
    ``` console
    {"agent":{"mbox":"mailto:janedoe@example.com","objectType":"Agent","name":null},"scopes":["statements/read","statements/write"]}
    ```

=== "HTTPie"

    ``` 
    http -a janedoe:supersecret :8100/whoami 
    ```
    ``` console
    HTTP/1.1 200 OK
    content-length: 107
    content-type: application/json
    date: Tue, 07 Nov 2023 17:32:31 GMT
    server: uvicorn

    {
        "agent": {
            "mbox": "mailto:janedoe@example.com",
            "name": null,
            "objectType": "Agent"
        },
        "scopes": [
            "statements/read",
            "statements/write"
        ]
    }
    ```

Congrats! 🎉 You have been successfully authenticated!

!!! tip "HTTP Basic auth caching"

    HTTP Basic auth implementation uses the secure and standard bcrypt algorithm to hash/salt passwords before storing them.
    This implementation comes with a performance cost.

    To speed up requests, credentials are stored in an LRU cache with a "Time To Live".

    To configure this cache, you can define the following environment variables:

    - the maximum number of entries in the cache. Select a value greater than the maximum number of individual user credentials, for better performance. Defaults to 100. 

    ```bash
    RALPH_AUTH_CACHE_MAX_SIZE=100
    ```
    - the "Time To Live" of the cache entries in seconds. Defaults to 3600s.

    ```bash
    RALPH_AUTH_CACHE_TTL=3600
    ```
