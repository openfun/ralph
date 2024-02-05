# How to use Ralph LRS?

This tutorial shows you how to run Ralph LRS, step by step.

!!! warning

    Ralph LRS will be executed locally for demonstration purpose.
    If you want to deploy Ralph LRS on a production server, please refer to the 
    [deployment guide](../helm.md).

Ralph LRS is based on [FastAPI](https://fastapi.tiangolo.com/). In this tutorial, we
will run the server manually with [Uvicorn](https://www.uvicorn.org/), but other
alternatives exists ([Hypercorn](https://pgjones.gitlab.io/hypercorn/),
[Daphne](https://github.com/django/daphne)).

!!! info "Prerequisites"

    Some tools are required to run the commands of this tutorial. Make sure they are installed first:

    - Ralph package with CLI optional dependencies, _e.g._ `pip install ralph-malph[cli]` (check the [CLI tutorial](../cli.md))
    - [Docker Compose](https://docs.docker.com/compose/)
    - [curl](https://curl.se/) or [httpie](https://httpie.io/)
