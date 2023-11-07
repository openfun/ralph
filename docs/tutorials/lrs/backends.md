# Backends

Ralph LRS is built to be used with a database instead of writing learning records in a local file.

Ralph LRS supports the following databases:

- Elasticsearch
- Mongo
- ClickHouse

Let's add the service of your choice to the `docker-compose.yml` file:

=== "Elasticsearch"
  
    ``` yaml title="docker-compose.yml" hl_lines="4-19 25-26"
    version: "3.9"

    services:
      db:
        image: elasticsearch:8.1.0
        environment:
          discovery.type: single-node
          xpack.security.enabled: "false"
        ports:
          - "9200:9200"
        mem_limit: 2g
        ulimits:
          memlock:
            soft: -1
            hard: -1
        healthcheck:
          test: curl --fail http://localhost:9200/_cluster/health?wait_for_status=green || exit 1
          interval: 1s
          retries: 60

      lrs:
        image: fundocker/ralph:latest
        environment:
          RALPH_APP_DIR: /app/.ralph
          RALPH_RUNSERVER_BACKEND: es
          RALPH_BACKENDS__LRS__ES__HOSTS: http://db:9200
        ports:
          - "8100:8100"
        command:
          - "uvicorn"
          - "ralph.api:app"
          - "--proxy-headers"
          - "--host"
          - "0.0.0.0"
          - "--port"
          - "8100"
        volumes:
          - .ralph:/app/.ralph
    ``` 

    We can now start the database service and wait for it to be up and healthy:
    ```bash
    docker compose up -d --wait db
    ```

    Before using Elasticsearch, we need to create an index, which we call `statements` for this example:
    === "curl"

        ```bash
        curl -X PUT http://localhost:9200/statements
        ```

    === "HTTPie"

        ```bash
        http PUT :9200/statements
        ```

=== "Mongo"

    ``` yaml title="docker-compose.yml" hl_lines="4-11 17-18"
    version: "3.9"

    services:
      db:
        image: mongo:5.0.9
        ports:
          - "27017:27017"
        healthcheck:
          test: mongosh --eval 'db.runCommand("ping").ok' localhost:27017/test --quiet
          interval: 1s
          retries: 60

      lrs:
        image: fundocker/ralph:latest
        environment:
          RALPH_APP_DIR: /app/.ralph
          RALPH_RUNSERVER_BACKEND: mongo
          RALPH_BACKENDS__LRS__MONGO__CONNECTION_URI: mongodb://db:27017
        ports:
          - "8100:8100"
        command:
          - "uvicorn"
          - "ralph.api:app"
          - "--proxy-headers"
          - "--host"
          - "0.0.0.0"
          - "--port"
          - "8100"
        volumes:
          - .ralph:/app/.ralph
    ``` 
    We can now start the database service and wait for it to be up and healthy:
    ```bash
    docker compose up -d --wait db
    ```

=== "ClickHouse"

    ``` yaml title="docker-compose.yml" hl_lines="4-22 28-30"
    version: "3.9"

    services:
      db:
        image: clickhouse/clickhouse-server:23.1.1.3077-alpine
        environment:
          CLICKHOUSE_DB: xapi
          CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
        ports:
          - 8123:8123
          - 9000:9000
        # ClickHouse needs to maintain a lot of open files, so they
        # suggest running the container with increased limits:
        # https://hub.docker.com/r/clickhouse/clickhouse-server/#!
        ulimits:
          nofile:
            soft: 262144
            hard: 262144
        healthcheck:
          test:  wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1
          interval: 1s
          retries: 60

      lrs:
        image: fundocker/ralph:latest
        environment:
          RALPH_APP_DIR: /app/.ralph
          RALPH_RUNSERVER_BACKEND: clickhouse
          RALPH_BACKENDS__LRS__CLICKHOUSE__HOST: db
          RALPH_BACKENDS__LRS__CLICKHOUSE__PORT: 8123
        ports:
          - "8100:8100"
        command:
          - "uvicorn"
          - "ralph.api:app"
          - "--proxy-headers"
          - "--host"
          - "0.0.0.0"
          - "--port"
          - "8100"
        volumes:
          - .ralph:/app/.ralph
    ``` 
    We can now start the database service and wait for it to be up and healthy:
    ```bash
    docker compose up -d --wait db
    ```

    Before using ClickHouse, we need to create a table in the `xapi` database, which we call `xapi_events_all`:
    
    === "curl"
        ```bash
          echo "CREATE TABLE xapi.xapi_events_all (
            event_id UUID NOT NULL,
            emission_time DateTime64(6) NOT NULL,
            event String NOT NULL
            )
            ENGINE MergeTree ORDER BY (emission_time, event_id)
            PRIMARY KEY (emission_time, event_id)" | \
          curl --data-binary @- "http://localhost:8123/"
        ```
    === "HTTPie"
        ```bash
          echo "CREATE TABLE xapi.xapi_events_all (
            event_id UUID NOT NULL,
            emission_time DateTime64(6) NOT NULL,
            event String NOT NULL
            )
            ENGINE MergeTree ORDER BY (emission_time, event_id)
            PRIMARY KEY (emission_time, event_id)" | \
          http :8123
        ```

Then we can start Ralph LRS:
```bash
docker compose up -d lrs
```

We can finally send some xAPI statements to Ralph LRS:

=== "curl"

    ```bash
    curl -sL https://github.com/openfun/ralph/raw/master/data/statements.json.gz | \
    gunzip | \
    head -n 100 | \
    jq -s . | \
    curl \
      --user janedoe:supersecret \
      -H "Content-Type: application/json" \
      -X POST \
      -d @- \
      "http://localhost:8100/xAPI/statements"
    ```

=== "HTTPie"

    ```bash
    curl -sL https://github.com/openfun/ralph/raw/master/data/statements.json.gz | \
    gunzip | \
    head -n 100 | \
    jq -s . | \
    http -a janedoe:supersecret POST :8100/xAPI/statements
    ```


And fetch, them back: 

=== "curl"

    ```bash
    curl \
      --user janedoe:supersecret \
      -X GET \
      "http://localhost:8100/xAPI/statements"
    ```

=== "HTTPie"

    ```bash
    http -a janedoe:supersecret :8100/xAPI/statements
    ```
