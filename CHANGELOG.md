# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added 

- Implement asynchronous part of `lrs` backend
- Define new `http` backend type 

### Changed

- Upgrade `fastapi` to `0.95.0`
- Upgrade `sentry_sdk` to `1.17.0`
- Upgrade `uvicorn` to `0.21.1`

### Fixed

- An issue with starting Ralph in pre-built Docker containers

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
- Add an official Helm Chart (experimental)
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

- Implement edx video browser events pydantic models
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

- Implement edx problem interaction events pydantic models
- Implement edx textbook interaction events pydantic models
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
- `convert` command to transform edx events to xAPI format
- EdX to xAPI converters for page `viewed` and`page_close` events
- Implement core event format converter
- xAPI video `played` pydantic models
- xAPI page `viewed` and page `terminated` pydantic models
- Implement edx navigational events pydantic models
- Implement edx enrollment events pydantic models
- Install security updates in project Docker images
- Model selector to retrieve associated pydantic model of a given event
- `validate` command to lint edx events using pydantic models
- Support all available bulk operation types for the elasticsearch backend
  (create, index, update, delete) using the `--es-op-type` option

### Changed

- Upgrade `elasticsearch` to `7.13.2`
- Upgrade `python-swiftclient` to `3.12.0`
- Upgrade `click` to `8.0.1`
- Upgrade `click-option-group` to `0.5.3`
- Upgrade `pydantic` to `1.8.2`
- Upgrade `sentry_sdk` to `1.1.0`
- Rename edx models
- Migrate model tests from factories to hypothesis strategies
- Tray: switch from openshift to k8s (BC)
- Tray: remove useless deployment probes

### Fixed

- Tray: remove `version` immutable field in DC selector

## [1.2.0] - 2021-02-26

### Added

- EdX server event pydantic model and factory
- EdX page_close browser event pydantic model and factory
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

[unreleased]: https://github.com/openfun/ralph/compare/v3.5.0...master
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
