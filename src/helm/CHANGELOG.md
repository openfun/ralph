# Changelog

All notable changes to the helm chart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [0.2.0] - 2023-11-08

### Added

- Add variable ``ingress.hosts``

### Changed

- Improve chart modularity
- Fix clickhouse version
- Improve volumes and ingress configurations

### Removed

- Remove variable ``ingress.hostname`` and ``ingress.tls``

## [0.1.0] - 2023-06-30

### Added

- Add an official Helm Chart (experimental)

[unreleased]: https://github.com/openfun/ralph/tree/master/src/helm
[0.2.0]: https://github.com/openfun/ralph/releases/tag/helm-v0.2.0
[0.1.0]: https://github.com/openfun/ralph/releases/tag/helm-v0.1.0
