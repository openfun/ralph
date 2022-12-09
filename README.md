# Ralph

Ralph is a toolbox for your learning analytics, it can be used as a:

- **library**, to fetch learning events from various backends, (de)serialize or
  convert them from various standard formats such as
  [xAPI](https://adlnet.gov/projects/xapi/),
- **command-line interface** (CLI), to build data pipelines the UNIX-way™️,
- **HTTP API server**, to collect xAPI statements (learning events)
  following the [ADL LRS
  standard](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#partthree).

## Quick start guide

Ralph is distributed as a standard python package; it can be installed _via_
`pip` or any other python package manager (_e.g_ Poetry, Pipenv, etc.):

```sh
# Install the full package
$ pip install \
    ralph-malph[backend-es,backend-ldp,backend-mongo,backend-swift,backend-ws,cli,lrs]

# Install only the core package (library usage without backends, CLI and LRS)
$ pip install ralph-malph
```

If you installed the full package (including the CLI, LRS and supported
backends), the `ralph` command should be available in your `PATH`. Try to
invoke the program usage thanks to the `--help` flag:

```
$ ralph --help
```

You should see a list of available commands and global flags for `ralph`. Note
that each command has its own usage that can be invoked _via_:

```
$ ralph COMMAND --help
```

> You should substitute `COMMAND` by the target command, _e.g._ `list`, to see
> its usage.

## Documentation

We try our best to maintain an up-to-date reference documentation for this
project. If you intend to install, test or contribute to ralph, we invite you
to read this [documentation](https://openfun.github.io/ralph) and give us
feedback if some parts are unclear or your use case is not (or poorly) covered.

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommandations from our
[handbook](https://handbook.openfun.fr).

## License

This work is released under the MIT License (see [LICENSE](./LICENSE.md)).
