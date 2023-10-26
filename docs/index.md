<p align="center">
  <a href="https://openfun.github.io/ralph"><img src="https://raw.githubusercontent.com/openfun/logos/main/ralph/ralph-color-dark.png" alt="Ralph logo" width="400"></a>
</p>

<p align="center">
    <em>⚙️ The ultimate toolbox for your learning analytics (expect some xAPI ❤️) </em>
</p>

<p align="center">
<a href="https://circleci.com/gh/openfun/ralph/tree/master">
    <img src="https://img.shields.io/circleci/build/gh/openfun/ralph/master?label=Tests&logo=circleci" alt="CircleCI tests">
</a>
<a href="https://pypi.org/project/ralph-malph">
    <img src="https://img.shields.io/pypi/v/ralph-malph?label=PyPi+package" alt="PyPi version">
</a>
<a href="https://pypi.org/project/ralph-malph">
    <img src="https://img.shields.io/pypi/pyversions/ralph-malph?label=Python" alt="Python versions">
</a>
<a href="https://hub.docker.com/r/fundocker/ralph/tags">
    <img src="https://img.shields.io/docker/v/fundocker/ralph/latest?label=Docker+image" alt="Docker image version">
</a>
</p>

Ralph is a toolbox for your learning analytics, it can be used as a:

- **[LRS](https://en.wikipedia.org/wiki/Learning_Record_Store)**, a HTTP API server to collect xAPI statements (learning events), following the [ADL LRS standard](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#partthree)
- **command-line interface** (CLI), to build data pipelines the UNIX-way™️,
- **library**, to fetch learning events from various backends, (de)serialize or
    convert them from and to various standard formats such as
    [xAPI](https://adlnet.gov/projects/xapi/), or
    [openedx](https://docs.openedx.org/en/latest/developers/references/internal_data_formats/tracking_logs/index.html)

## Installation

### Install from PyPI

Ralph is distributed as a standard python package; it can be installed _via_
`pip` or any other python package manager (_e.g._ Poetry, Pipenv, etc.):

???+ tip "Use a virtual environment for installation"

    To maintain a clean and controlled environment when installing `ralph-malph`, consider using a [virtual environment](https://docs.python.org/3/library/venv.html).
    
    - Create a virtual environment:
    ```bash
    python3.12 -m venv <path-to-virtual-environment>
    ```

    - Activate the virtual environment:
    ```bash
    source venv/bin/activate
    ```

If you only need to integrate [learning statement models](./models/index.md) feature in your project, you don't need to
install the `backends`, `cli` or `lrs` extra dependencies, the **core library** is what you need:

```bash
pip install ralph-malph
```

If you want to use the [Ralph LRS server](./api/index.md), add the `lrs` flavour in your installation. 
You also have to choose the type of backend you will use for LRS data storage (`backend-clickhouse`,`backend-es`,`backend-mongo`).

- Install the **core package** with the LRS and the Elasticsearch backend. For example:

```bash
pip install ralph-malph[backend-es,lrs]
```

- Add the `cli` flavour if you want to use the LRS on the command line: 

```bash
pip install ralph-malph[backend-es,lrs,cli]
```

- If you have various uses for Ralph's features or would like to discover all the existing functionnalities, it is recommended to install the **full package**: 

```bash
pip install ralph-malph[backend-clickhouse,backend-es,backend-ldp,backend-lrs,backend-mongo,backend-s3,backend-swift,backend-ws,cli,lrs]
```

### Install from DockerHub

Ralph is distributed as a [Docker
image](https://hub.docker.com/repository/docker/fundocker/ralph). If
[Docker](https://docs.docker.com/get-docker/) is installed on your machine, it
can be pulled from DockerHub:

``` bash
docker run --rm -i fundocker/ralph:latest ralph --help
```

???+ tip "Use a `ralph` alias in your local environment"

    Simplify your workflow by creating an alias for easy access to Ralph commands:

    ```bash
    alias ralph="docker run --rm -i fundocker/ralph:latest ralph"
    ```

## [WIP] Start using Ralph


## Contributing to Ralph

If you're interested in contributing to Ralph, whether it's by reporting issues, suggesting improvements, or submitting code changes, please head over to our dedicated [Contributing to Ralph](./contribute.md) page. 
There, you'll find detailed guidelines and instructions on how to take part in the project.

We look forward to your contributions and appreciate your commitment to making Ralph a more valuable tool for everyone.

## Contributors

<a href="https://github.com/openfun/ralph/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=openfun/ralph" />
</a>

## License

This work is released under the MIT License (see [LICENSE](./LICENSE.md)).
