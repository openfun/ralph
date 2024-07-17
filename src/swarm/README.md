# Deploy Ralph with Docker Swarm

## Prerequisites

Before proceeding with the deployment of Ralph, ensure that you have Docker Engine
installed and configured with Swarm mode: [Docker
Engine](https://docs.docker.com/engine/install/).

## Tutorial

This tutorial provides a step-to-step guide to deploying Ralph on a local Docker
Engine cluster in swarm mode. By following this tutorial, you will:

- set up a small cluster consisting of one manager node on your local machine,
- deploy Ralph using the production Compose file.

> ⚠️ Caution! In this tutorial:
> - We are setting up a cluster with only one manager node and no workers. For a more
>   reliable setup in a real-world scenario, it's recommended to create a cluster with
>   one manager node and multiple worker nodes (refer to the Docker
>   [documentation](https://docs.docker.com/engine/swarm/how-swarm-mode-works/nodes/)).

> - We assume that an Elasticsearch cluster is already deployed and is accessible.

### Initializing the cluster

Initialize a local cluster using the following command:
```bash
docker swarm init
```

To view the current state of the swarm, use:
```bash
docker info
```

For informations about nodes in the swarm, execute:
```bash
docker node ls
```

> 💡 Tip 
> If you want to add more nodes to the cluster, refer to this
> [documentation](https://docs.docker.com/engine/swarm/swarm-tutorial/add-nodes/).

### Configuring environment variables

All Ralph environment variables can be set in the file `env.d/ralph.env`.
Change the `RALPH_BACKENDS__LRS__ES__HOSTS` variable with your Elasticsearch cluster credentials.

### Configuring Ralph authentication

The default method for securing the Ralph API server is HTTP Basic Authentication.
For this, we need to create a user in Ralph LRS.

To create new user credentials, refer to the [HTTP Basic Authentication](../../docs/tutorials/lrs/authentication/basic.md) documentation.

You should replace the `env.d/auth.json` file with your newly created file.

### Creating Logging

Adjust service logging configuration by creating a new `config` object from the
project's sources:

```bash
docker config create logging_config env.d/logging-config.yaml
```

This command creates a new config named `logging_config` from the content of
`env.d/logging-config.yaml`. This config is mounted under the `/app/`
directory of the `ralph` service during the deployment.


### Creating the Network

To enable service-to-service communication, create an overlay network and attach
services to it. In the `docker-compose.prod.yml` file, `ralph` service is connected to
the `backend` network, which needs to be created:
```bash
docker network create -d overlay --attachable backend
```

Ensure Ralph is connected to an Elasticsearch instance for storing statements. If
using Docker Swarm to deploy Elasticsearch, make sure both services are running on the same `backend` network.

### Deploying Ralph

Docker Engine in swarm mode can deploy services defined in a Compose file.

Adjust the `docker-compose.prod.yml` file and the environment file `ralph.env` as per
your requirements, including Ralph's docker image tags.

Once ready, deploy the service using the command: 
```bash
docker stack deploy lrs --compose-file docker-compose.prod.yml --with-registry-auth
```

Check if the service is up and running with:
```bash
docker service ls
```

View the running containers with:
```bash
docker ps
```

For investigating further in case a service is not healthy, use:
```bash
docker inspect --format "{{json .State.Health }}" CONTAINER_ID | jq
```
_Note_: this command requires that [jq](https://jqlang.github.io/jq/) is installed
on your operating system.

### Exposing Ralph with Caddy

To make Ralph accessible to external tools and  Learning Management System (LMS), we
will utilize [Caddy](https://caddyserver.com/docs/install) as a reverse proxy. While
Caddy can be launched via its CLI, we strongly recommend employing a service manager for
automatic restarts (refer to the [documentation](https://caddyserver.com/docs/running)).

Begin by creating a Caddyfile which contains your configuration:
```
ralph.example.com {
reverse_proxy :8080
}
```

Launch Caddy from the directory containing the Caddyfile with the command:
```bash
caddy start
```

Caddy is now operational, directing traffic to your pods.
