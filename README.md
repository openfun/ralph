# Ralph

Ralph, is a command-line tool to fetch, extract, convert and push your tracking
logs (_aka_ learning events) from various storage backends to your LRS or any
other compatible storage or database backend.

## Quick start guide

Ralph is distributed as a standard python package; it can be installed _via_
`pip` or any other python package manager (_e.g_ Poetry, Pipenv, etc.):

```
$ pip install ralph-malph
```

Once installed, the `ralph` command should be available in your `PATH`. Try to
invoke the program usage thanks to the `--help` flag:

```
$ ralph --help
```

You should see a list of available commands and global flags for `ralph`. Note
that each command has its own usage that can be invoked _via_:

```
$ ralph COMMAND --help
```

> You should sustitute `COMMAND` by the target command, _e.g._ `list`, to see
> its usage.

## Documentation

We try our best to maintain an up-to-date reference documentation for this
project. If you intend to install, test or contribute to ralph, we invite you
to read this [documentation](https://openfun.github.io/ralph) and give us
feedback if some parts are unclear or your use-case is not (or poorly) covered.

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommandations from our
[handbook](https://openfun.gitbooks.io/handbook/content).

## License

This work is released under the MIT License (see [LICENSE](./LICENSE.md)).
