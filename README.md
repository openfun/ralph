# Ralph, a learning analytics processor to feed your LRS

## Getting started with development

### Core development

To start playing with `ralph`, you should build it using the `bootstrap` Make target:

```
$ make bootstrap
```

Now you can start playing the CLI:

```
$ bin/ralph --help
```

To lint your code, either use the `lint` meta target or one of the linting tools we use:

```bash
# Run all linters
$ make lint

# Run pylint
$ make lint-pylint

# List available linters
$ make help | grep lint-
```

To run tests on your code, either use the `test` Make target or the
`bin/pytest` script to pass specific arguments to the test runner:

```bash
# Run all tests
$ make test

# Run pytest with options
$ bin/pytest -x -k mixins
```

### Tray development

Ralph is distributed along with its tray (a deployable package for Kubernetes
clusters using [Arnold](https://github.com/openfun/arnold)). If you intend to
work on this tray, please refer to Arnold's documentation.

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommandations from our
[handbook](https://openfun.gitbooks.io/handbook/content).

## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
