<p align="center">
  <a href="https://openfun.github.io/ralph"><img src="https://raw.githubusercontent.com/openfun/logos/main/ralph/ralph-color-dark.png" alt="Ralph logo" width="400"></a>
</p>

<p align="center">
    <em>⚙️ The ultimate toolbox for your learning analytics (expect some xAPI ❤️) </em>
</p>

<p align="center">
<a href="https://circleci.com/gh/openfun/ralph/tree/main">
    <img src="https://img.shields.io/circleci/build/gh/openfun/ralph/main?label=Tests&logo=circleci" alt="CircleCI tests">
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

- **LRS**, an HTTP API server to collect xAPI statements (learning events), following the [ADL LRS standard](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#part-three-data-processing-validation-and-security)
- [**command-line interface**](./tutorials/cli.md) (CLI), to build data pipelines the UNIX-way™️,
- [**library**](./tutorials/library.md), to fetch learning events from various backends, (de)serialize or
    convert them from and to various standard formats such as
    [xAPI](https://adlnet.gov/projects/xapi/), or
    [openedx](https://docs.openedx.org/en/latest/developers/references/internal_data_formats/tracking_logs/index.html)

## What is an LRS?

A Learning Record Store, or LRS, is a key component in the context of learning analytics and the Experience API (xAPI).

The [Experience API](https://github.com/adlnet/xAPI-Spec) (or Tin Can API) is a standard for tracking and reporting learning experiences. 
In particular, it defines:

- the [xAPI format](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#part-two-experience-api-data) of the learning events. xAPI statements include an `actor`, a `verb`, an `object` as well as contextual information. Here's an example statement: 
```json
{
    "id": "12345678-1234-5678-1234-567812345678",
    "actor":{
        "mbox":"mailto:xapi@adlnet.gov"
    },
    "verb":{
        "id":"http://adlnet.gov/expapi/verbs/created",
        "display":{
            "en-US":"created"
        }
    },
    "object":{
        "id":"http://example.adlnet.gov/xapi/example/activity"
    }
}
```
- the [Learning Record Store](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#part-three-data-processing-validation-and-security) (LRS), is a RESTful API that collects, stores and retrieves these events. Think of it as a learning database that unifies data from various learning platforms and applications. 
These events can come from an LMS (*Moodle*, *edX*), or any other learning component that supports sending xAPI statements to an LRS (e.g. an embedded video player), from various platforms.


!!! info "xAPI specification version"
    In Ralph, we're following the xAPI specification **1.0.3** that you can find [here](https://github.com/adlnet/xAPI-Spec/tree/master).

    For your information, xAPI specification **2.0** is out! It's not currently supported in Ralph, but you can check it [here](https://opensource.ieee.org/xapi).

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

If you want to generate xAPI statements from your application and only need to integrate [learning statement models](./features/models.md) in your project, you don't need to
install the `backends`, `cli` or `lrs` extra dependencies, the **core library** is what you need:

```bash
pip install ralph-malph
```

If you want to use the [Ralph LRS server](./features/api.md), add the `lrs` flavour in your installation. 
You also have to choose the type of backend you will use for LRS data storage (`backend-clickhouse`,`backend-es`,`backend-mongo`).

- Install the **core package** with the LRS and the Elasticsearch backend. For example:

```bash
pip install ralph-malph[backend-es,lrs]
```

- Add the `cli` flavour if you want to use the LRS on the command line: 

```bash
pip install ralph-malph[backend-es,lrs,cli]
```

- If you want to play around with backends with Ralph as a library, you can install: 

```bash
pip install ralph-malph[backends]
```

- If you have various uses for Ralph's features or would like to discover all the existing functionnalities, it is recommended to install the **full package**: 

```bash
pip install ralph-malph[full]
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

## LRS specification compliance

WIP.

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
