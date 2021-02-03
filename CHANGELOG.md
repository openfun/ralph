# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for Swift storage backend
- Use the `push` command `--force` option to ignore ES bulk import errors
- The elasticsearch backend now accepts passing all supported client options

### Changed

- Remove click_log package dependency
- Upgrade pyyaml to 5.4.1
- Upgrade pandas to 1.2.1

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

[unreleased]: https://github.com/openfun/v1.0.0...master
[1.0.0]: https://github.com/openfun/ashley/compare/3d03d85...v1.0.0
