# Backends for data storage

Ralph supports various backends that can be accessed to read from or write to (learning events or random data).
Implemented backends are listed below along with their configuration parameters. 
If your favourite data storage method is missing, feel free to submit your implementation or get in touch!

## Key concepts

Each backend has its own parameter requirements. These
parameters can be set as command line options or environment variables; the
later is the **recommended solution** for sensitive data such as service
credentials. For example, the `os_username` (OpenStack user name) parameter
of the OpenStack Swift backend, can be set as a command line option using
`swift` as the option prefix (and replacing underscores in its name by dashes):

```bash
ralph list --backend swift --swift-os-username johndoe # [...] more options
```

Alternatively, this parameter can be set as an environment variable (in upper
case, prefixed by the program name, _e.g._ `RALPH_`):

```bash
export RALPH_BACKENDS__DATA__SWIFT__OS_USERNAME="johndoe"
ralph list --backend swift # [...] more options
```

The general patterns for backend parameters are:

- `--{{ backend_name }}-{{ parameter | underscore_to_dash }}` for command options, and,
- `RALPH_BACKENDS__DATA__{{ backend_name | uppercase }}__{{ parameter | uppercase }}` for environment variables.

## Elasticsearch

Elasticsearch backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch indexed data from it.

### ::: ralph.backends.data.es.ESDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## MongoDB

MongoDB backend is mostly used for indexation purpose (as a datalake) but
it can also be used to fetch collections of documents from it.

### ::: ralph.backends.data.mongo.MongoDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## ClickHouse

The ClickHouse backend can be used as a data lake and to fetch collections of
documents from it.

### ::: ralph.backends.data.clickhouse.ClickHouseDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

The ClickHouse client options supported in Ralph can be found in these locations:

- [Python driver specific](https://clickhouse.com/docs/en/integrations/language-clients/python/driver-api#settings-argument)
- [General ClickHouse client settings](https://clickhouse.com/docs/en/operations/settings/settings/)

## OVH - Log Data Platform (LDP)

LDP is a nice service built by OVH on top of Graylog to follow, analyse and
store your logs. Learning events (_aka_ tracking logs) can be stored in GELF
format using this backend.

!!! info "Read-only backend"

    For now the LDP backend is **read-only** as we consider that it is mostly
    used to collect primary logs and not as a Ralph target. Feel free to get in
    touch to prove us wrong, or better: submit your proposal for the `write`
    method implementation.

To access OVH's LDP API, you need to register Ralph as an authorized
application and generate an application key, an application secret and a
consumer key.

While filling the registration form available at:
[eu.api.ovh.com/createToken/](https://eu.api.ovh.com/createToken/), be sure to
give an appropriate validity time span to your token and allow only GET
requests on the `/dbaas/logs/*` path.

### ::: ralph.backends.data.ldp.LDPDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

For more information about OVH's API client parameters, please refer to the
project's documentation:
[github.com/ovh/python-ovh](https://github.com/ovh/python-ovh).

## OpenStack Swift

Swift is the OpenStack object storage service. This storage backend is fully
supported (read and write operations) to stream and store log archives.

Parameters correspond to a standard authentication using
OpenStack Keystone service and configuration to work with the target container.

### ::: ralph.backends.data.swift.SwiftDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## Amazon S3

S3 is the Amazon Simple Storage Service. This storage backend is fully
supported (read and write operations) to stream and store log archives.

Parameters correspond to a standard authentication with AWS CLI 
and configuration to work with the target bucket.

### ::: ralph.backends.data.s3.S3DataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## File system

The file system backend is a dummy template that can be used to develop your own backend. 
It is a "dummy" backend as it is not intended for practical use (UNIX `ls` and `cat` would be more practical).

The only required parameter is the `path` we want to list or stream content from.

### ::: ralph.backends.data.fs.FSDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## Learning Record Store (LRS)

The LRS backend is used to store and retrieve xAPI statements from various systems that follow the [xAPI specification](https://github.com/adlnet/xAPI-Spec/tree/master) (such as our own Ralph LRS, which can be run from this package). 
LRS systems are mostly used in e-learning infrastructures.

### ::: ralph.backends.data.lrs.LRSDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

## WebSocket

The webSocket backend is **read-only** and can be used to get real-time events.

> If you use OVH's Logs Data Platform (LDP), you can retrieve a WebSocket URI to test your
> data stream by following instructions from the
> [official documentation](https://docs.ovh.com/gb/en/logs-data-platform/ldp-tail/#retrieve-your-websocket-address).

### ::: ralph.backends.data.async_ws.WSDataBackendSettings
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members: 
        - attributes

### ::: ralph.backends.data.async_ws.WSClientOptions
    handler: python
    options:
      show_root_heading: false
      show_source: false
      members:
        - attributes
