# Upgrade

All instructions to upgrade this project from one release to the next will be documented in this file. Upgrades must be run sequentially, meaning you should not skip minor/major releases while upgrading (fix releases can be skipped).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### 4.x to 5.y

#### Upgrade learning events models

xAPI learning statements validator and converter are built with Pydantic. Ralph 5.x
is compatible with Pydantic 2.x. Please refer to [Pydantic migration
guide](https://docs.pydantic.dev/dev/migration/) if you are using Ralph `models`
feature.

> Most of fields in Pydantic models that are optional are set with `None` as
  default value in Ralph 5.y. If you serialize some Pydantic models from ralph
  and want to keep the same content in your serialization, please set
  `exclude_none` to `True` in the serialization method `model_dump`.
 
### 3.x to 4.y

#### Upgrade user credentials
To conform to xAPI specifications, we need to represent users as xAPI Agents. You must therefore delete and re-create the credentials file using the updated cli, OR you can modify it directly to add the `agents` field. The credentials file is located in `{ RALPH_APP_DIR }/{ RALPH_AUTH_FILE }` (defaults to `.ralph/auth.json`). Each user profile must follow the following pattern (see [this post](https://xapi.com/blog/deep-dive-actor-agent/) for examples of valid agent objects) :

```
{
  "username": "USERNAME_UNCHANGED",
  "hash": "PASSWORD_HASH_UNCHANGED",
  "scopes": [ LIST_OF_SCOPES_UNCHANGED ],
  "agent": { A_VALID_AGENT_OBJECT }
}
```
Agent can take one of the following forms, as specified by the [xAPI specification](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#2423-inverse-functional-identifier):
- mbox: 
```
"agent": {
      "mbox": "mailto:john.doe@example.com"
}
```
- mbox_sha1sum:
```
"agent": {
        "mbox_sha1sum": "ebd31e95054c018b10727ccffd2ef2ec3a016ee9",
}
```
- openid:
```
"agent": {
      "openid": "http://foo.openid.example.org/"
}
```
- account:
```
"agent": {
      "account": {
        "name": "simonsAccountName",
        "homePage": "http://www.exampleHomePage.com"
}
```

For example here is a valid `auth.json` file: 

```
[
  {
    "username": "john.doe@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["example_scope"],
    "agent": {
      "mbox": "mailto:john.doe@example.com"
    }
  },
  {
    "username": "simon.says@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["second_scope", "third_scope"],
    "agent": {
      "account": {
        "name": "simonsAccountName",
        "homePage": "http://www.exampleHomePage.com"
      }
    }
  }
]
```

#### Upgrade Ralph CLI usage

If you are using Ralph's CLI, the following changes may affect you:

- The `ralph fetch` command changed to `ralph read`
  - The `-b ws` backend option changed to `-b async_ws`
    - The corresponding `--ws-uri` option changed to `--async-ws-uri`
  - The `-c --chunk-size` option changed to `-s --chunk-size`
  - The `DEFAULT_BACKEND_CHUNK_SIZE` environment variable configuration is removed in
    favor of allowing each backend to define their own defaults:

    | Backend           | Environment variable for default (read) chunk size    |
    |-------------------|-------------------------------------------------------|
    | async_es/es       | RALPH_BACKENDS__DATA__ES__READ_CHUNK_SIZE=500         |
    | async_lrs/lrs     | RALPH_BACKENDS__DATA__LRS__READ_CHUNK_SIZE=500        |
    | async_mongo/mongo | RALPH_BACKENDS__DATA__MONGO__READ_CHUNK_SIZE=500      |
    | clickhouse        | RALPH_BACKENDS__DATA__CLICKHOUSE__READ_CHUNK_SIZE=500 |
    | fs                | RALPH_BACKENDS__DATA__FS__READ_CHUNK_SIZE=4096        |
    | ldp               | RALPH_BACKENDS__DATA__LDP__READ_CHUNK_SIZE=4096       |
    | s3                | RALPH_BACKENDS__DATA__S3__READ_CHUNK_SIZE=4096        |
    | swift             | RALPH_BACKENDS__DATA__SWIFT__READ_CHUNK_SIZE=4096     |

- The `ralph push` command changed to `ralph write`
  - The `-c --chunk-size` option changed to `-s --chunk-size`
  - The `DEFAULT_BACKEND_CHUNK_SIZE` environment variable configuration is removed in
    favor of allowing each backend to define their own defaults:

    | Backend           | Environment variable for default (write) chunk size    |
    |-------------------|--------------------------------------------------------|
    | async_es/es       | RALPH_BACKENDS__DATA__ES__WRITE_CHUNK_SIZE=500         |
    | async_lrs/lrs     | RALPH_BACKENDS__DATA__LRS__WRITE_CHUNK_SIZE=500        |
    | async_mongo/mongo | RALPH_BACKENDS__DATA__MONGO__WRITE_CHUNK_SIZE=500      |
    | clickhouse        | RALPH_BACKENDS__DATA__CLICKHOUSE__WRITE_CHUNK_SIZE=500 |
    | fs                | RALPH_BACKENDS__DATA__FS__WRITE_CHUNK_SIZE=4096        |
    | ldp               | RALPH_BACKENDS__DATA__LDP__WRITE_CHUNK_SIZE=4096       |
    | s3                | RALPH_BACKENDS__DATA__S3__WRITE_CHUNK_SIZE=4096        |
    | swift             | RALPH_BACKENDS__DATA__SWIFT__WRITE_CHUNK_SIZE=4096     |

- Environment variables used to configure backend options for CLI usage
  (read/write/list commands) changed their prefix:
  `RALPH_BACKENDS__{{DATABASE or HTTP or STORAGE or STREAM}}__{{BACKEND}}__{{OPTION}}`
  changed to
  `RALPH_BACKENDS__DATA__{{BACKEND}}__{{OPTION}}`
- Environment variables used to configure backend options for LRS usage
  (runserver command) changed their prefix:
  `RALPH_BACKENDS__{{DATABASE}}__{{BACKEND}}__{{OPTION}}`
  changed to
  `RALPH_BACKENDS__LRS__{{BACKEND}}__{{OPTION}}`

#### Upgrade history syntax

CLI syntax has been changed from `fetch` & `push` to `read` & `write` affecting the command history. You must replace the command history after updating:
- locate your history file path, which is in `{ RALPH_APP_DIR }/history.json` (defaults to `.ralph/history.json`)
- run the commands below to update history

```bash
sed -i 's/"fetch"/"read"/g' { my_history_file_path }
sed -i 's/"push"/"write"/g' { my_history_file_path }
```

#### Upgrade Ralph library usage (backends)

If you use Ralph's backends in your application, the following changes might affect you:

Backends from `ralph.backends.database`, `ralph.backends.http`, `ralph.backends.stream`,
and `ralph.backends.storage` packages have moved to a single `ralph.backends.data`
package.

| Ralph v3 (database/http/storage/stream) backends        | Ralph v4 data backends                                 |
|---------------------------------------------------------|--------------------------------------------------------|
| `ralph.backends.database.clickhouse.ClickHouseDatabase` | `ralph.backends.data.clickhouse.ClickHouseDataBackend` |
| `ralph.backends.database.es.ESDatabase`                 | `ralph.backends.data.es.ESDataBackend`                 |
| `ralph.backends.database.mongo.MongoDatabase`           | `ralph.backends.data.mongo.MongoDataBackend`           |
| `ralph.backends.http.async_lrs.AsyncLRSHTTP`            | `ralph.backends.data.async_lrs.AsyncLRSDataBackend`    |
| `ralph.backends.http.lrs.LRSHTTP`                       | `ralph.backends.data.lrs.LRSDataBackend`               |
| `ralph.backends.storage.fs.FSStorage`                   | `ralph.backends.data.fs.FSDataBackend`                 |
| `ralph.backends.storage.ldp.LDPStorage`                 | `ralph.backends.data.ldp.LDPDataBackend`               |
| `ralph.backends.storage.s3.S3Storage`                   | `ralph.backends.data.s3.S3DataBackend`                 |
| `ralph.backends.storage.swift.SwiftStorage`             | `ralph.backends.data.swift.SwiftDataBackend`           |
| `ralph.backends.stream.ws.WSStream`                     | `ralph.backends.data.async_ws.AsyncWSDataBackend`      |

LRS-specific `query_statements` and `query_statements_by_ids` database backend methods
have moved to a dedicated `ralph.backends.lrs.BaseLRSBackend` interface that extends the
data backend interface with these two methods.

The `query_statements_by_ids` method return type changed to `Iterator[dict]`.

| Ralph v3 database backends for lrs usage                | Ralph v4 LRS data backends                             |
|---------------------------------------------------------|--------------------------------------------------------|
| `ralph.backends.database.clickhouse.ClickHouseDatabase` | `ralph.backends.lrs.clickhouse.ClickHouseLRSBackend`   |
| `ralph.backends.database.es.ESDatabase`                 | `ralph.backends.lrs.es.ESLRSBackend`                   |
| `ralph.backends.database.mongo.MongoDatabase`           | `ralph.backends.lrs.mongo.MongoLRSBackend`             |

**Backend interface differences**

- Data backends are read-only by default
- Data backends that support write operations inherit from the
  `ralph.backends.data.base.Writable` interface
- Data backends that support list operations inherit from the
  `ralph.backends.data.base.Listable` interface
- Data backends that support LRS operations
  (`query_statements`/`query_statements_by_ids`) inherit from the
  `ralph.backends.lrs.BaseLRSBackend` interface
- `__init__(self, **kwargs)` changed to `__init__(self, settings: DataBackendSettings)`
  where each DataBackend defines it's own Settings object
  For example the `FSDataBackend` uses `FSDataBackendSettings`
- `stream` and `get` methods changed to `read`
- `put` methods changed to `write`

**Backend usage migration example**

Ralph v3 using `ESDatabase`:

```python
from ralph.conf import ESClientOptions
from ralph.backends.database.es import ESDatabase, ESQuery

# Instantiate the backend.
backend = ESDatabase(
  hosts="localhost",
  index="statements"
  client_options=ESClientOptions(verify_certs=False)
)
# Read records from backend.
query = ESQuery(query={"query": {"term": {"modulo": 0}}})
es_statements = list(backend.get(query))

# Write records to backend.
backend.put([{"id": 1}])
```

Ralph v4 using `ESDataBackend`:

```python
from ralph.backends.data.es import (
  ESClientOptions,
  ESDataBackend,
  ESDataBackendSettings,
  ESQuery,
)

# Instantiate the backend.
settings = ESDataBackendSettings(
  HOSTS="localhost",
  INDEX="statements",
  CLIENT_OPTIONS=ESClientOptions(verify_certs=False)
)
backend = ESDataBackend(settings)

# Read records from backend.
query = ESQuery(query={"term": {"modulo": 0}})
es_statements = list(backend.read(query))

# Write records to backend.
backend.write([{"id": 1}])
```

#### Upgrade ClickHouse schema

If you are using the ClickHouse backend, schema changes have been made
to drop the existing JSON column in favor of the String version of the 
same data. See [this issue](https://github.com/openfun/ralph/issues/482) 
for details. 

Ralph does not manage the ClickHouse schema, so if you have existing 
data you will need to manually alter it as an admin user. Note: this 
will rewrite the statements table, which may take a long time if you
have many rows. The command to run is:

```sql
-- If RALPH_BACKENDS__DATA__CLICKHOUSE__DATABASE is 'xapi'
-- and RALPH_BACKENDS__DATA__CLICKHOUSE__EVENT_TABLE_NAME is 'test'

ALTER TABLE xapi.test DROP COLUMN event, RENAME COLUMN event_str to event;
```
