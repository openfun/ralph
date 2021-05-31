# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

### Changed

- Upgrade `elasticsearch` to `7.13.1`
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

[unreleased]: https://github.com/openfun/ralph/compare/v1.2.0...master
[1.2.0]: https://github.com/openfun/ralph/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/openfun/ralph/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/openfun/ralph/compare/3d03d85...v1.0.0
