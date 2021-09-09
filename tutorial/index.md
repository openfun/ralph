# Learn how to use Ralph

> This tutorial is intended for new or beginning users of `ralph`.
> It is required to have some knowledge of the UNIX system flows, basic notions in data management.
> An understanding of edX and xAPI learning data standardization formats is preferred.

_Nota : In this tutorial, it is considered your machine is on Linux distribution.
If you are working on Windows, we highly recommend you either to use a machine on Linux
or to install [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install)._

## Let's start !

With this tutorial, you are going to get hands on with ralph for the first time.
All you need is `ralph`, free time and motivation to successfully complete it.

There are no difficulty, take a deep breath and let's go!

You are going to stream data between two backends among the ones available on `ralph`.
To get to it, you will use all ralph commands.

### Install ralph

`ralph` should be installed correctly. Follow the
[Quick start guide](https://openfun.github.io/ralph/#quick_start_guide) if you have not yet
installed it locally (via a virtual environment or with the Docker image).

### Set your playing environment

```
# create a folder for this tutorial on your desired location
$ mkdir ralph-tutorial

# download data files
$ cd ralph-tutorial
$ wget <data-url> # or from playground ?

```

> Note: For more convenience, it is advised to keep all the test data in the `/data` folder.

### Choose your backends

`ralph` provides a wide range of [backend types](https://openfun.github.io/ralph/backends),
you can process data between database, logging, storage and stream backends.

According to the input backend type you choose, the tutorial and the input data may differ.
We invite you to, first choose, the backend types, you need and then to click on the corresponding ling to access the tutorial.

- [Input `database` backend tutorial](./database.md)
- [Input `logging` backend tutorial](./logging.md)
- [Input `storage` backend tutorial](./storage.md)
- [Input `stream` backend tutorial](./stream.md)

<!-- FIXME Along the redaction of the tutorial and depending on the incoming data,
some parts of the specificity of the tutorial will be summed up in this file
(for e.g. push the data in the input which is normally identical for the whole backends. TBDiscussed) -->
