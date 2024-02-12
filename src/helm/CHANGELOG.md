# Changelog

All notable changes to the helm chart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Changed

- Upgrade appVersion to `4.1.0`

## [0.3.0] - 2024-02-07

### Added

- A NOTE.txt file with instructions for chart users
- A ConfigMap template for Ralph configuration
- A ConfigMap for logging configuration
- A secret Manifest for helping user configure Ralph
- A Helm connection test for Ralph

### Changed

- Upgrade appVersion to `4.0.0`
- Environment variables are now provided through a ConfigMap and a Secret
- Improve Ingress configuration
- Improved values based on Helm chart template file 

### Removed

- Dependencies to mongodb and clickhouse (managed outside of chart scope)
- Secrets template and vault values (managed outside of chart scope)

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

[unreleased]: https://github.com/openfun/ralph/tree/main/src/helm
[0.3.0]: https://github.com/openfun/ralph/releases/tag/helm-v0.3.0
[0.2.0]: https://github.com/openfun/ralph/releases/tag/helm-v0.2.0
[0.1.0]: https://github.com/openfun/ralph/releases/tag/helm-v0.1.0
