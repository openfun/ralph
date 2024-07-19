# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fix type of `statement.result.score.scaled` from `int` to `Decimal`

## [5.0.1] - 2024-07-11

### Changed

- Force Elasticsearch REFRESH_AFTER_WRITE setting to be a string

### Fixed

- Fix LaxStatement validation to prevent statements IDs modification

## [5.0.0] - 2024-05-02

### Added

- Models: Add Webinar xAPI activity type

### Changed

- Upgrade `pydantic` to `2.7.0`
- Migrate model tests from hypothesis strategies to polyfactory
- Replace soon-to-be deprecated `parse_obj_as` with `TypeAdapter`

## [4.2.0] - 2024-04-08

### Added

- Models: Add Edx teams-related events support
- Models: Add Edx notes events support
- Models: Add Edx certificate events support
- Models: Add Edx bookmark (renamed Course Resource) events support
- Models: Add Edx poll and survey events support
- Models: Add Edx Course Content Completion events support
- Models: Add Edx drag and drop events support
- Models: Add Edx cohort events support
- Models: Add Edx content library interaction events support
- Backends: Add `ralph.backends.data` and `ralph.backends.lrs` entry points
  to discover backends from plugins.

### Changed

- Backends: the first argument of the `get_backends` method now requires a list
  of `EntryPoints`, each pointing to a backend class, instead of a tuple of
  packages containing backends.
- API: The `RUNSERVER_BACKEND` configuration value is no longer validated to
  point to an existing backend.

### Fixed

- LRS: Fix querying on `activity` when LRS contains statements with an object
  lacking a `objectType` attribute

## [4.1.0] - 2024-02-12

### Added

- Add LRS multitenancy support for user-specific target storage

### Changed

- `query_statements` and `query_statements_by_ids` methods can now take an
optional user-specific target

### Fixed

- Backends: switch LRSStatementsQuery since/until field types to iso 8601 string

### Removed

- Removed `event_table_name` attribute of the ClickHouse data backend

## [4.0.0] - 2024-01-23

### Added

- Backends: Add `Writable` and `Listable` interfaces to distinguish supported
  functionalities among `data` backends
- Backends: Add `max_statements` option to data backends `read` method
- Backends: Add `prefetch` option to async data backends `read` method
- Backends: Add `concurrency` option to async data backends `write` method
- Backends: Add `get_backends` function to automatically discover backends
  for CLI and LRS usage
- Backends: Add client options for WSDataBackend
- Backends: Add `READ_CHUNK_SIZE` and `WRITE_CHUNK_SIZE` data backend settings
- Models: Implement Pydantic model for LRS Statements resource query parameters
- Models: Implement xAPI LMS Profile statements validation
- Models: Add `EdX` to `xAPI` converters for enrollment events
- Project: Add aliases for `ralph-malph` extra dependencies: `backends` and
  `full`

### Changed

- Arnold: Add variable to override PVC name in arnold deployment
- API: `GET /statements` now has "mine" option which matches statements that
  have an authority field matching that of the user
- API: Invalid parameters now return 400 status code
- API: Forwarding PUT now uses PUT (instead of POST)
- API: Incoming statements are enriched with `id`, `timestamp`, `stored`
  and `authority`
- API: Add `RALPH_LRS_RESTRICT_BY_AUTHORITY` option making `?mine=True`
  implicit
- API: Add `RALPH_LRS_RESTRICT_BY_SCOPE` option enabling endpoint access
  control by user scopes
- API: Enhance 'limit' query parameter's validation
- API: Variable `RUNSERVER_AUTH_BACKEND` becomes `RUNSERVER_AUTH_BACKENDS`, and
  multiple authentication methods are supported simultaneously
- Backends: Refactor LRS Statements resource query parameters defined for
  `ralph` API
- Backends: Refactor `database`, `storage`, `http` and `stream` backends under
  the unified `data` backend interface [BC]
- Backends: Refactor LRS `query_statements` and `query_statements_by_ids`
  backends methods under the unified `lrs` backend interface [BC]
- Backends: Update `statementId` and `voidedStatementId` to snake_case,
  with camelCase alias, in `LRSStatementsQuery`
- Backends: Replace reference to a JSON column in ClickHouse with
  function calls on the String column [BC]
- CLI: User credentials must now include an "agent" field which can be created
  using the cli
- CLI: Change `push` to `write` and `fetch` to `read` [BC]
- CLI: Change `-c --chunk-size` option to `-s --chunk-size` [BC]
- CLI: Change websocket backend name `-b ws` to `-b async_ws` along with it's
  uri option `--ws-uri` to `--async-ws-uri` [BC]
- CLI: List cli usage strings in alphabetical order
- CLI: Change backend configuration environment variable prefixes from
  `RALPH_BACKENDS__{{DATABASE|HTTP|STORAGE|STREAM}}__{{BACKEND}}__{{OPTION}}`
  to `RALPH_BACKENDS__DATA__{{BACKEND}}__{{OPTION}}`
- Models: The xAPI `context.contextActivities.category` field is now mandatory
  in the video and virtual classroom profiles. [BC]
- Upgrade base python version to 3.12 for the development stack and Docker
  image
- Upgrade `bcrypt` to `4.1.2`
- Upgrade `cachetools` to `5.3.2`
- Upgrade `fastapi` to `0.108.0`
- Upgrade `sentry_sdk` to `1.39.1`
- Upgrade `uvicorn` to `0.25.0`

### Fixed

- API: Fix a typo ('attachements' -> 'attachments') to ensure compliance with
  the LRS specification and prevent potential silent bugs

### Removed

- Project: Drop support for Python 3.7
- Models: Remove `school`, `course`, `module` context extensions in Edx to xAPI
  base converter
- Models: Remove `name` field in `VideoActivity` xAPI model mistakenly used in
  `video` profile
- CLI: Remove `DEFAULT_BACKEND_CHUNK_SIZE` environment variable configuration

## [3.9.0] - 2023-07-21

### Changed

- Upgrade `fastapi` to `0.100.0`
- Upgrade `sentry_sdk` to `1.28.1`
- Upgrade `uvicorn` to `0.23.0`
- Enforce valid IRI for `activity` parameter in `GET /statements`
- Change how duplicate xAPI statements are handled for `clickhouse` backend

## [3.8.0] - 2023-06-21

### Added

- Implement edX open response assessment events pydantic models
- Implement edx peer instruction events pydantic models
- Implement xAPI VideoDownloaded pydantic model
  (using xAPI TinCan `downloaded` verb)

### Changed

- Allow to use a query for HTTP backends in the CLI

## [3.7.0] - 2023-06-13

### Added

- Implement asynchronous `async_lrs` backend
- Implement synchronous `lrs` backend
- Implement xAPI virtual classroom pydantic models
- Allow to insert custom endpoint url for S3 service
- Cache the HTTP Basic auth credentials to improve API response time
- Support OpenID Connect authentication method

### Changed

- Clean xAPI pydantic models naming convention
- Upgrade `fastapi` to `0.97.0`
- Upgrade `sentry_sdk` to `1.25.1`
- Set Clickhouse `client_options` to a dedicated pydantic model
- Upgrade `httpx` to `0.24.1`
- Force a valid (JSON-formatted) IFI to be passed for the `/statements`
GET query `agent` filtering
- Upgrade `cachetools` to `5.3.1`

### Removed

- `verb`.`display` field no longer mandatory in xAPI models and for converter

## [3.6.0] - 2023-05-17

### Added

- Allow to ignore health check routes for Sentry transactions

### Changed

- Upgrade `sentry_sdk` to `1.22.2`
- Upgrade `uvicorn` to `0.22.0`
- LRS `/statements` `GET` method returns a code 400 with certain parameters
as per the xAPI specification
- Use batch/v1 api in cronjob_pipeline manifest
- Use autoscaling/v2 in HorizontalPodAutoscaler manifest

### Fixed

- Fix the `more` IRL building in LRS `/statements` GET requests

## [3.5.1] - 2023-04-18

### Changed

- Upgrade `httpx` to `0.24.0`
- Upgrade `fastapi` to `0.95.1`
- Upgrade `sentry_sdk` to `1.19.1`
- Upgrade `uvicorn` to `0.21.1`

### Fixed

- An issue with starting Ralph in pre-built Docker containers
- Fix double quoting in ClickHouse backend server parameters
- An issue Ralph starting when ClickHouse is down

## [3.5.0] - 2023-03-08

### Added

- Implement PUT verb on statements endpoint
- Add ClickHouse database backend support

### Changed

- Make trailing slashes optional on statements endpoint
- Upgrade `sentry_sdk` to `1.16.0`

## [3.4.0] - 2023-03-01

### Changed

- Upgrade `fastapi` to `0.92.0`
- Upgrade `sentry_sdk` to `1.15.0`

### Fixed

- Restore sentry integration in the LRS server

## [3.3.0] - 2023-02-03

### Added

- Restore python 3.7+ support for library usage (models)

### Changed

- Allow xAPI extra fields in `extensions` fields

## [3.2.1] - 2023-02-01

### Changed

- Relax required Python version to `3.7`+

## [3.2.0] - 2023-01-25

### Added

- Add a new `auth` subcommand to generate required credentials file for the LRS
- Implement support for AWS S3 storage backend
- Add CLI `--version` option

### Changed

- Upgrade `fastapi` to `0.89.1`
- Upgrade `httpx` to `0.23.3`
- Upgrade `sentry_sdk` to `1.14.0`
- Upgrade `uvicorn` to `0.20.0`
- Tray: add the `ca_certs` path for the ES backend client option (LRS)
- Improve Sentry integration for the LRS
- Update handbook link to `https://handbook.openfun.fr`
- Upgrade base python version to 3.11 for the development stack and Docker
  image

### Fixed

- Restore ES and Mongo backends ability to use client options


## [3.1.0] - 2022-11-17

### Added

- EdX to xAPI converters for video events

### Changed

- Improve Ralph's library integration by unpinning dependencies (and prefer
  ranges)
- Upgrade `fastapi` to `0.87.0`

### Removed

- ModelRules constraint

## [3.0.0] - 2022-10-19

### Added

- Implement edX video browser events pydantic models
- Create a `post` endpoint for statements implementing the LRS spec
- Implement support for the MongoDB database backend
- Implement support for custom queries when using database backends `get`
  method (used in the `fetch` command)
- Add dotenv configuration file support and `python-dotenv` dependency
- Add `host` and `port` options for the `runserver` cli command
- Add support for database selection when running the Ralph LRS server
- Implement support for xAPI statement forwarding
- Add database backends `status` checking
- Add `health` LRS router
- Tray: add LRS server support

### Changed

- Migrate to `python-legacy` handler for `mkdocstrings` package
- Upgrade `click` to `8.1.3`
- Upgrade `elasticsearch` to `8.3.3`
- Upgrade `fastapi` to `0.79.1`
- Upgrade `ovh` to `1.0.0`
- Upgrade `pydantic` to `1.9.2`
- Upgrade `pymongo` to `4.2.0`
- Upgrade `python-keystoneclient` to `5.0.0`
- Upgrade `python-swiftclient` to `4.0.1`
- Upgrade `requests` to `2.28.1`
- Upgrade `sentry_sdk` to `1.9.5`
- Upgrade `uvicorn` to `0.18.2`
- Upgrade `websockets` to `10.3`
- Make backends yield results instead of writing to standard streams (BC)
- Use pydantic settings management instead of global variables in defaults.py
- Rename backend and parser parameter environment variables (BC)
- Make project dependencies management more modular for library usage

### Removed

- Remove YAML configuration file support and `pyyaml` dependency (BC)

### Fixed

- Tray: do not create a cronjobs list when no cronjob has been defined
- Restore history mixin logger

## [2.1.0] - 2022-04-13

### Added

- Implement edX problem interaction events pydantic models
- Implement edX textbook interaction events pydantic models
- `ws` websocket stream backend (compatible with the `fetch` command)
- bundle `jq`, `curl` and `wget` in the `fundocker/ralph` Docker image
- Tray: enable ralph app deployment command configuration
- Add a `runserver` command with basic auth and a `Whoami` route
- Create a `get` endpoint for statements implementing the LRS spec
- Add optional fields to BaseXapiModel

### Changed

- Upgrade `uvicorn` to `0.17.4`
- Upgrade `elasticsearch` to `7.17.0`
- Upgrade `sentry_sdk` to `1.5.5`
- Upgrade `fastapi` to `0.73.0`
- Upgrade `pyparsing` to `3.0.7`
- Upgrade `pydantic` to `1.9.0`
- Upgrade `python-keystoneclient` to `4.4.0`
- Upgrade `python-swiftclient` to `3.13.0`
- Upgrade `pyyaml` to `6.0`
- Upgrade `requests` to `2.27.1`
- Upgrade `websockets` to `10.1`

## [2.0.1] - 2021-07-15

### Changed

- Upgrade `elasticsearch` to `7.13.3`

### Fixed

- Restore elasticsearch backend datastream compatibility for bulk operations

## [2.0.0] - 2021-07-09

### Added

- xAPI video `interacted` pydantic models
- xAPI video `terminated` pydantic models
- xAPI video `completed` pydantic models
- xAPI video `seeked` pydantic models
- xAPI video `initialized` pydantic models
- xAPI video `paused` pydantic models
- `convert` command to transform edX events to xAPI format
- EdX to xAPI converters for page `viewed` and`page_close` events
- Implement core event format converter
- xAPI video `played` pydantic models
- xAPI page `viewed` and page `terminated` pydantic models
- Implement edX navigational events pydantic models
- Implement edX enrollment events pydantic models
- Install security updates in project Docker images
- Model selector to retrieve associated pydantic model of a given event
- `validate` command to lint edX events using pydantic models
- Support all available bulk operation types for the elasticsearch backend
  (create, index, update, delete) using the `--es-op-type` option

### Changed

- Upgrade `elasticsearch` to `7.13.2`
- Upgrade `python-swiftclient` to `3.12.0`
- Upgrade `click` to `8.0.1`
- Upgrade `click-option-group` to `0.5.3`
- Upgrade `pydantic` to `1.8.2`
- Upgrade `sentry_sdk` to `1.1.0`
- Rename edX models
- Migrate model tests from factories to hypothesis strategies
- Tray: switch from openshift to k8s (BC)
- Tray: remove useless deployment probes

### Fixed

- Tray: remove `version` immutable field in DC selector

## [1.2.0] - 2021-02-26

### Added

- edX server event pydantic model and factory
- edX page_close browser event pydantic model and factory
- Tray: allow to specify a self-generated elasticsearch cluster CA certificate

### Fixed

- Tray: add missing Swift variables in the secret
- Tray: fix pods anti-affinity selector

### Removed

- `pandas` is no longer required

## [1.1.0] - 2021-02-04

### Added

- Support for Swift storage backend
- Use the `push` command `--ignore-errors` option to ignore ES bulk import
  errors
- The elasticsearch backend now accepts passing all supported client options

### Changed

- Upgrade `pyyaml` to `5.4.1`
- Upgrade `pandas` to `1.2.1`

### Removed

- `click_log` is no longer required as we are able to configure logging

## [1.0.0] - 2021-01-13

### Added

- Implement base CLI commands (list, extract, fetch & push) for supported
  backends
- Support for ElasticSearch database backend
- Support for LDP storage backend
- Support for FS storage backend
- Parse (gzipped) tracking logs in GELF format
- Support for application's configuration file
- Add optional sentry integration
- Distribute Arnold's tray to deploy Ralph in a k8s cluster as cronjobs

[unreleased]: https://github.com/openfun/ralph/compare/v5.0.1...main
[5.0.1]: https://github.com/openfun/ralph/compare/v5.0.0...v5.0.1
[5.0.0]: https://github.com/openfun/ralph/compare/v4.2.0...v5.0.0
[4.2.0]: https://github.com/openfun/ralph/compare/v4.1.0...v4.2.0
[4.1.0]: https://github.com/openfun/ralph/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/openfun/ralph/compare/v3.9.0...v4.0.0
[3.9.0]: https://github.com/openfun/ralph/compare/v3.8.0...v3.9.0
[3.8.0]: https://github.com/openfun/ralph/compare/v3.7.0...v3.8.0
[3.7.0]: https://github.com/openfun/ralph/compare/v3.6.0...v3.7.0
[3.6.0]: https://github.com/openfun/ralph/compare/v3.5.1...v3.6.0
[3.5.1]: https://github.com/openfun/ralph/compare/v3.5.0...v3.5.1
[3.5.0]: https://github.com/openfun/ralph/compare/v3.4.0...v3.5.0
[3.4.0]: https://github.com/openfun/ralph/compare/v3.3.0...v3.4.0
[3.3.0]: https://github.com/openfun/ralph/compare/v3.2.1...v3.3.0
[3.2.1]: https://github.com/openfun/ralph/compare/v3.2.0...v3.2.1
[3.2.0]: https://github.com/openfun/ralph/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/openfun/ralph/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/openfun/ralph/compare/v2.1.0...v3.0.0
[2.1.0]: https://github.com/openfun/ralph/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/openfun/ralph/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/openfun/ralph/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/openfun/ralph/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/openfun/ralph/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/openfun/ralph/compare/3d03d85...v1.0.0
