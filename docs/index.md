# Introduction

Ralph is a command-line tool to fetch, extract, convert and push your tracking
logs (_aka_ learning events) from various storage backends to your LRS or any
other compatible storage or database backend.

## Key concepts

Ralph has been designed to batch process your logs using base commands and UNIX
standard streams (`stdin`, `stdout`) to connect them in a pipeline that fits
your needs. A base example pipeline may be:

```sh
$ ralph fetch --backend swift my_archive.gzip | \
    gunzip | \
    ralph push --backend es
```

In this small pipeline, we stream `my_archive.gzip` content from a Swift
container to the standard output (using the `fetch` command), uncompress the
content (using the `gunzip` command), and bulk insert logs in an ElasticSearch
index (using the `push` command).

As UNIX is beautiful, Ralph offers many powerful possibilities by combining its
commands with other standard commands or command line tools.

## Quick start guide

Ralph is distributed as a python package and a Docker image.

> If you choose to install `ralph` in your native environment (without using
> Docker), please make sure that **Python 3.9** is installed (and your default
> python distribution).

Ralph package can be installed from PyPI using the `pip` tool:

```sh
# Create a new virtualenv (optional)
$ python3.9 -m venv venv
$ source venv/bin/activate

# Install the full package (in a virtualenv)
(venv) $ pip install ralph-malph[backend-es,backend-ldp,backend-mongo,backend-swift,backend-ws,cli,lrs]

# Install only the core package with the Elasticsearch backend and the LRS (in a virtualenv)
(venv) $ pip install ralph-malph[backend-es,lrs]

# Test the ralph command (it should be in your PATH)
(venv) $ ralph --help
```

If you only need to integrate `ralph` models in your project, you don't need to
install the `backends`, `cli` or `lrs` extra dependencies, the core package is
what you need:

```sh
# Install the core library (in a virtualenv)
(venv) $ pip install ralph-malph
```

Alternatively, Docker users can pull the latest `ralph` image and start playing
with it:

```sh
# Pull latest docker image and get usage
$ docker run --rm -i fundocker/ralph:latest ralph --help

# Pro tip: define an alias to ease your life
$ alias ralph="docker run --rm -i fundocker/ralph:latest ralph"
```

Now that `ralph` can be run from your system, we invite you to explore
[available commands](./commands.md).

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any questions related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommendations from our
[handbook](https://openfun.gitbooks.io/handbook/content).

## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
