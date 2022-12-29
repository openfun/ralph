# Backends

Ralph supports various storage and database backends that can be accessed to
read from or write learning events to. Implemented backends are listed below
along with their configuration parameters. If your favourite backend is missing
to the list, feel free to submit your implementation or get in touch!

## Key concepts

We distinguish storage from database backends as the semantic and concepts are
quite different in terms of code, but those two types of backends can be
considered as "backends" from a Ralph user perspective as the CLI can use both
in most of its commands.

Each backend has its own parameters that are required to use it. Those
parameters can be set as command line options or environment variables; the
later is the **recommended solution** for sensible data such as service
credentials. If we consider the `os_username` (OpenStack user name) parameter
of the OpenStack Swift backend, it can be set as a command line option using
`swift` as the option prefix (and replacing underscores in its name by dashes):

```bash
$ ralph list --backend swift --swift-os-username johndoe # [...] more options
```

Alternatively, this parameter can be set as an environment variable (in upper
case, prefixed by the program name, _e.g._ `RALPH_`):

```bash
$ export RALPH_BACKENDS__STORAGE__SWIFT__OS_USERNAME="johndoe"
$ ralph list --backend swift # [...] more options
```

The general patterns for backend parameters are:

- `--{{ backend_name }}-{{ parameter | underscore_to_dash }}` for command options, and,
- `RALPH_BACKENDS__{{ backend_type | uppercase }}__{{ backend_name | uppercase }}__{{ parameter | uppercase }}` for environment variables, where the `backend_type` is one of `DATABASE`, `STORAGE` and `STREAM`.

## Storage backends

### OVH - Log Data Platform (LDP)

LDP is a nice service built by OVH on top of Graylog to follow, analyse and
store your logs. Learning events (_aka_ tracking logs) can be stored in GELF
format using this backend.

> For now the LDP backend is **read-only** as we consider that it is mostly
> used to collect primary logs and not as a Ralph target. Feel free to get in
> touch to prove us wrong, or better: submit your proposal for the `write`
> method implementation.

#### Backend parameters

To access OVH's LDP API, you need to register Ralph as an authorized
application and generate an application key, an application secret and a
consumer key.

While filling the registration form available at:
[eu.api.ovh.com/createToken/](https://eu.api.ovh.com/createToken/), be sure to
give an appropriate validity time span to your token and allow only GET
requests on the `/dbaas/logs/*` path.

- `endpoint`: the API endpoint (_e.g._ `ovh-eu`)
- `application_key`: use generated application key
- `application_secret`: use generated application secret
- `consumer_key`: use generated consumer key

The following parameters are required to fetch archives from an LDP account
stream:

- `service_name`: the LDP account name (_e.g._ `ldp-xx-xxxxx`)
- `stream_id`: the identifier of the stream you are querying (_e.g._ a UUID hex
  representation: `77ec6e4a-ac15-4bcf-8043-7429bf275e49`)

For more information about OVH's API client parameters, please refer to the
project's documentation:
[github.com/ovh/python-ovh](https://github.com/ovh/python-ovh).

### OpenStack Swift

Swift is the OpenStack object storage service. This storage backend is fully
supported (read and write operations) to stream and store log archives.

#### Backend parameters

Primarily required parameters correspond to a standard authentication using
OpenStack Keystone service:

- `os_identity_api_version`: keystone API version you will authenticate to (defaults to `3`)
- `os_auth_url`: the authentication URL (defaults to OVH's Swift `https://auth.cloud.ovh.net/`)
- `os_project_domain_name`: the project domain name (defaults to `Default`)
- `os_user_domain_name`: the user domain name (defaults to `Default`)
- `os_username`: the name of your openstack swift user
- `os_password`: the password of your openstack swift user

Secondary parameters are required to work with the target container:

- `os_storage_url`: the URL of the target container
- `os_region_name`: the region where your container is
- `os_tenant_name`: the name of the tenant of your container
- `os_tenant_id`: the identifier of the tenant of your container

### Amazon S3

S3 is the Amazon Simple Storage Service. This storage backend is fully
supported (read and write operations) to stream and store log archives.

#### Backend parameters

Primarily required parameters correspond to a standard authentication with AWS CLI:

- `access_key_id`: the access key for your AWS account
- `secret_access_key`: the secret key for your AWS account
- `session_token`: the session key for your AWS account (only needed when you are using
temporary credentials).

Secondary parameters are required to work with the target bucket:

- `default_region`: the region where your bucket is
- `bucket_name`: the name of your S3 bucket

### File system

The file system backend is a dummy template that can be used to develop your
own backend. It's a "dummy" backend as it's not required in a UNIX Shell
context, the `ls` and `cat` commands used along with UNIX streams will do a
better job.

#### Backend parameters

The only required parameter is the `path` we want to list or stream content
from.

## Stream backends

### WebSocket

The webSocket backend is **read-only** and can be used to get real-time events.

> If you use OVH's Logs Data Platform (LDP), you can retrieve a WebSocket URI to test your
> data stream by following instructions from the
> [official documentation](https://docs.ovh.com/gb/en/logs-data-platform/ldp-tail/#retrieve-your-websocket-address).

#### Backend parameters

- `ws_uri`: the WebSocket uri (_e.g._ `wss://example.com/websocket`)

## Database backends

### Elasticsearch

Elasticsearch backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch indexed data from it.

#### Backend parameters

Elasticsearch backend parameters required to connect to a cluster are:

- `hosts`: a list of cluster hosts to connect to (_e.g._ `["http://elasticsearch-node:9200"]`)
- `index`: the elasticsearch index where to get/put documents
- `client_options`: a comma separated key=value list of Elasticsearch client options

The Elasticsearch client options supported in Ralph are:
- `ca_certs`: the path to the CA certificate file.
- `verify_certs`: enable or disable the certificate verification. Note that it should be enabled in production. Default to `True`

### MongoDB

MongoDB backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch collections of documents from it.

#### Backend parameters

MongoDB backend parameters required to connect to a cluster are:

- `connection_uri`: the connection URI to connect to (_e.g._ `["mongodb://mongo:27017/"]`)
- `database`: the database to connect to
- `collection`: the collection to get/put objects to
- `client_options`: a comma separated key=value list of MongoDB client options

The MongoDB client options supported in Ralph are:
- `document_class`: default class to use for documents returned from queries
- `tz_aware`: if True, datetime instances returned as values in a document will be timezone aware (otherwise they will be naive)


### ClickHouse

The ClickHouse backend can be used as a data lake and to fetch collections of
documents from it.

#### Backend parameters

ClickHouse parameters required to connect are:
        host: str = clickhouse_settings.HOST,
        port: int = clickhouse_settings.PORT,
        database: str = clickhouse_settings.DATABASE,
        event_table_name: str = clickhouse_settings.EVENT_TABLE_NAME,
        client_options: dict = clickhouse_settings.CLIENT_OPTIONS,
- `host`: the connection hostname to connect to (_e.g._ `"clickhouse.yourhost.com"`)
- `port`: the port to the ClickHouse HTTPS interface (_e.g._ `8123`)
- `database`: the name of the database to connect to
- `event_table_name`: the name of the table to write statements to
- `client_options`: a comma separated key=value list of ClickHouse client options

By default, the following client options are set, if you override the default 
client options you must also set these:
- `"date_time_input_format": "best_effort"` allows RFC date parsing
- `"allow_experimental_object_type": 1` allows the JSON data type we use to store statements

The ClickHouse client options supported in Ralph can be found in these locations:
- [Python driver specific](https://clickhouse.com/docs/en/integrations/language-clients/python/driver-api#settings-argument)
- [General ClickHouse client settings](https://clickhouse.com/docs/en/operations/settings/settings/)
