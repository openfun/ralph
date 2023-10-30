
<p align="center">
  <a href="https://openfun.github.io/ralph"><img src="https://raw.githubusercontent.com/openfun/logos/main/ralph/ralph-color-dark.png" alt="Ralph logo" width="400"></a>
</p>

<p align="center">
    <em>Ralph, the ultimate Learning Record Store (and more!) for your learning analytics</em>
</p>

<p align="center">
<a href="https://circleci.com/gh/openfun/ralph/tree/master">
    <img src="https://img.shields.io/circleci/build/gh/openfun/ralph/master?label=Tests&logo=circleci" alt="Tests Status">
</a>
<a href="https://pypi.org/project/ralph-malph">
    <img src="https://img.shields.io/pypi/v/ralph-malph?label=PyPI+package" alt="PyPI package version">
</a>
<a href="https://pypi.org/project/ralph-malph">
    <img src="https://img.shields.io/pypi/pyversions/ralph-malph?label=Python" alt="Python versions supported">
</a>
<a href="https://hub.docker.com/r/fundocker/ralph/tags">
    <img src="https://img.shields.io/docker/v/fundocker/ralph/latest?label=Docker+image" alt="Docker image version">
</a>
<a href="https://discord.gg/vYx6YWxJCS">
    <img src="https://img.shields.io/discord/1082704478463082496?label=Discord&logo=discord&style=shield" alt="Discord">
</a>
</p>

---

**Documentation**: [https://openfun.github.io/ralph](https://openfun.github.io/ralph)

**Source Code**: [https://github.com/openfun/ralph](https://github.com/openfun/ralph)

---

Ralph is a toolbox for your learning analytics, it can be used as a:

- **[LRS](https://en.wikipedia.org/wiki/Learning_Record_Store)**, a HTTP API server to collect xAPI statements (learning events), following the [ADL LRS standard](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#partthree)
- **command-line interface** (CLI), to build data pipelines the UNIX-way™️,
- **library**, to fetch learning events from various backends, (de)serialize or
    convert them from various standard formats such as
    [xAPI](https://adlnet.gov/projects/xapi/), or
    [openedx](https://docs.openedx.org/en/latest/developers/references/internal_data_formats/tracking_logs/index) html

## ⚡️ Quick start guide: Run the LRS server

> Preliminary notes:
>
> 1. [`curl`](https://curl.se), [`jq`](https://stedolan.github.io/jq/) and
>    [`docker compose`](https://docs.docker.com/compose/) are required to run
>    some commands of this tutorial. Make sure they are installed first.
>
> 2. In order to run the Elasticsearch backend locally on GNU/Linux operating
>    systems, ensure that your virtual memory limits are not too low and
>    increase them (temporally) if needed by typing this command from your
>    terminal (as `root` or using `sudo`): `sysctl -w vm.max_map_count=262144`
>
> Reference:
> https://www.elastic.co/guide/en/elasticsearch/reference/master/vm-max-map-count.html

To bootstrap a test environment on your machine, clone this project first and
run the `bootstrap` Makefile target:

```
$ make bootstrap
```

This command will create required `.env` file (you may want to edit it for your
test environment), build the Ralph's Docker image and start a single node
Elasticsearch cluster _via_ Docker compose.

You can check the `elasticsearch` service status using the `status` helper:

```bash
$ make status # This is an alias for: $ docker compose ps
```

You may now start the LRS server using:

```
$ make run
```

The server should be up and running at
[http://localhost:8100](http://localhost:8100). You can check its status using
the heartbeat probe:

```
$ curl http://localhost:8100/__heartbeat__
```

The expected answer should be:

```json
{"database":"ok"}
```

If the database status is satisfying, you are now ready to send xAPI statements
to the LRS:

```
$ curl -sL https://github.com/openfun/potsie/raw/main/fixtures/elasticsearch/lrs.json.gz | \
  gunzip | \
  head -n 100 | \
  sed "s/@timestamp/timestamp/g" | \
  jq -s . | \
  curl -Lk \
    --user ralph:secret \
    -X POST \
    -H "Content-Type: application/json" \
    http://localhost:8100/xAPI/statements/ -d @-
```

The command above fetches one hundred (100) example xAPI statements from our
[Potsie](https://github.com/openfun/potsie) project and sends them to the LRS
using `curl`.

You can get them back from the LRS using `curl` to query the
`/xAPI/statements/` endpoint:

```
$ curl -s \
    --user ralph:secret \
    -H "Content-Type: application/json" \
    http://localhost:8100/xAPI/statements/ \ |
  jq
```

> Note that using `jq` is optional in this case, it is used to improve response
> readability. It is not required to install it to run this snippet.

## ⚡️ Quick start guide: Manipulate data with the CLI

### With the Docker image

Ralph is distributed as a [Docker
image](https://hub.docker.com/repository/docker/fundocker/ralph). If
[Docker](https://docs.docker.com/get-docker/) is installed on your machine, it
can be pulled from DockerHub:

```
$ docker run --pull always --rm fundocker/ralph:latest ralph --help
```

### With the Python package

Ralph is distributed as a standard python package; it can be installed _via_
`pip` or any other python package manager (_e.g._ Poetry, Pipenv, etc.):

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

## Migrating

Some major version changes require updating persistence layers. Check out the [migration guide](https://github.com/openfun/ralph/blob/master/UPGRADE.md) for more information.

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommendations from our
[handbook](https://handbook.openfun.fr).

## Useful commands


You can explore all available rules using:

```
$ make help
```
but here are some of them:

- Bootstrap the project: `$ make bootstrap`
- Run tests: `$ make test`
- Run all linters: `$ make lint`
- If you add new dependencies to the project, you will have to rebuild the Docker
image (and the development environment): `$ make down && make bootstrap`

## License

This work is released under the MIT License (see [LICENSE](./LICENSE.md)).
