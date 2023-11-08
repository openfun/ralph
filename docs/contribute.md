# Contribute

## Ralph's core

To start playing with `ralph`, you should build it using the `bootstrap` Make target:

```
$ make bootstrap
```

Once the project has been bootstrapped, you may want to edit generated `.env`
file to set up available backends parameters that will be injected in the
running container as environment variables to configure Ralph (see [backends
documentation](./backends.md)):

```dotenv
# Elasticsearch backend
RALPH_ES_HOSTS=http://elasticsearch:9200
RALPH_ES_INDEX=statements
RALPH_ES_TEST_HOSTS=http://elasticsearch:9200
RALPH_ES_TEST_INDEX=test-index

# [...]
```

> Note that lines starting with a `#` are considered as commented and thus will
> have no effect while running Ralph.

Now you can start playing the CLI:

```
$ bin/ralph --help
```

To lint your code, either use the `lint` meta target or one of the linting tools we use:

```bash
# Run all linters
$ make lint

# Run ruff linter
$ make lint-ruff

# Run ruff linter and resolve fixable errors
$ make lint-ruff-fix

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

# Run pytest with options and more debugging logs
$ bin/pytest -x -vvv -s --log-level=DEBUG -k mixins
```

### Working with local backends

Not all backends are accessible in a local environment development; for now
only `elasticsearch` and `swift` services are accessible as docker containers
(see `docker-compose.yml` services).

To configure those backends, we provide default parameters in the `.env.dist`
template, you can copy/paste them in your `.env` file (and uncomment them so
that they are properly injected in running containers).

> In order to run the Elasticsearch backend locally on GNU/Linux operating
> systems, ensure that your virtual memory limits are not too low and increase
> them (temporally) if needed by typing this command from your terminal (as
> `root` or using `sudo`):
>
> `sysctl -w vm.max_map_count=262144`
>
> Reference:
> https://www.elastic.co/guide/en/elasticsearch/reference/master/vm-max-map-count.html

Once configured, start available backends using:

```bash
$ make run-[BACKEND]
```

Substitute `[BACKEND]` by the backend name, _e.g._ `es` for Elasticsearch or
`swift` for OpenStack Swift:

```bash
# Start Elasticsearch local backend
$ make run-es
# Start Swift local backend
$ make run-swift
# Start all local backends
$ make run-all
```

Now that you have started at least the `elasticsearch` and `swift` backends,
it's time to play with them:

```bash
# Store a JSON file in the Swift backend
$ echo '{"id": 1, "foo": "bar"}' | \
    ./bin/ralph write -b swift -f foo.json

# Check that we have created a new JSON file in the Swift backend
$ bin/ralph list -b swift
foo.json

# Read the content of the JSON file and index it in Elasticsearch
$ bin/ralph read -b swift foo.json | \
    bin/ralph write -b es

# Check that we have properly indexed the JSON file in Elasticsearch
$ bin/ralph read -b es
{"id": 1, "foo": "bar"}
```

## Ralph's tray

Ralph is distributed along with its tray (a deployable package for Kubernetes
clusters using [Arnold](https://github.com/openfun/arnold)). If you intend to
work on this tray, please refer to Arnold's documentation first.

Dependencies:

- [Kubectl](https://kubernetes.io/docs/tasks/tools/) (>`v.1.23.5`):
  This CLI is used to communicate with the running Kubernetes instance you
  will use.
- [k3d](https://k3d.io/) (>`v.5.0.0`): This tool is used to set up
  and run a lightweight Kubernetes cluster, in order to have a local
  environment (it is required to complete quickstart instructions below to
  avoid depending on an existing Kubernetes cluster).
- [curl](https://curl.se/) is required by Arnold's CLI.
- [gnupg](https://gnupg.org/) to encrypt Ansible vaults passwords and
  collaborate with your team.

### Create a local `k3d` cluster

To create (or run) a local kubernetes cluster, we use `k3d`. The cluster's
bootstrapping should be run _via_:

```bash
$ make k3d-cluster
```

> Running a k3d-cluster locally supposes that the 80 and 443 ports of your
> machine are available, so that the ingresses created for your project
> responds properly. If one or both ports are already used by another service
> running on your machine, the `make k3d-cluster` command may fail.

You can check that your cluster is running using the `k3d cluster` command:

```bash
$ k3d cluster list
NAME     SERVERS   AGENTS   LOADBALANCER
ralph    1/1       0/0      true
```

As you can see, we are running a single node cluster called `ralph`.

### Bootstrap an Arnold project

Once your Kubernetes cluster is running, you need to create a standard Arnold
project describing applications and environments you need to deploy:

```bash
$ make arnold-bootstrap
```

Once bootstrapped, Arnold should have created a `group_vars` directory
containing the following files:

```bash
$ tree group_vars
group_vars
├── common
└── customer
    └── ralph
        ├── development
        │   ├── main.yml
        │   └── secrets
        │       ├── databases.vault.yml
        │       ├── elasticsearch.vault.yml
        │       └── ralph.vault.yml
        └── main.yml

5 directories, 5 files
```

To create the LRS credentials file, you need to provide a list of accounts
allowed to request the LRS in Ralph's vault:

```bash
# Setup your kubernetes environment
$ source .k3d-cluster.env.sh

# Decrypt the vault
$ bin/arnold -d -c ralph -e development -- vault -a ralph decrypt
```

Edit the vault file to add a new account for the `foo` user with the `bar`
password and a relevant scope:

```yaml
# group_vars/customer/ralph/development/secrets/ralph.vault.yml
#
# [...]
#
# LRS
LRS_AUTH:
  - username: "foo"
    hash: "$2b$12$lCggI749U6TrzK7Qyr7xGe1KVSAXdPjtkMew.BD6lzIk//T5YSb72"
    scopes:
      - "foo_scope"
```

The password hash has been generated using `bcrypt` as explained in the [API
user guide](./api/#creating_a_credentials_file).

And finally (re-)encrypt Ralph's vault:

```bash
# Encrypt the vault
$ bin/arnold -d -c ralph -e development -- vault -a ralph encrypt
```

You are now ready to create the related Kubernetes Secret while initializing
Arnold project in the next step.

### Prepare working namespace

You are now ready to create required Kubernetes objects to start working on
Ralph's deployment:

```bash
$ make arnold-init
```

At this point an Elasticsearch cluster should be running on your Kubernetes
cluster:

```bash
$ kubectl -n development-ralph get -l app=elasticsearch pod
NAME                                         READY   STATUS      RESTARTS   AGE
elasticsearch-node-0                         1/1     Running     0          69s
elasticsearch-node-1                         1/1     Running     0          69s
elasticsearch-node-2                         1/1     Running     0          69s
es-index-template-j-221010-09h25m24s-nx5qz   0/1     Completed   0          49s
```

We are now ready to deploy Ralph to Kubernetes!

### Deploy, code, repeat

To test your local docker image, you need to build it and publish it to the
local kubernetes cluster docker registry using the `k3d-push` Makefile rule:

```bash
$ make k3d-push
```

> Note that each time you modify Ralph's application or its Docker image, you
> will need to make this update.

Now that your Docker image is published, it's time to deploy it!

```bash
$ make arnold-deploy
```

To test this deployment, let's try to make an authenticated request to the LRS:

```bash
$ curl -sLk \
    --user foo:bar \
    "https://$(\
        kubectl -n development-ralph \
        get \
        ingress/ralph-app-current \
        -o jsonpath='{.spec.rules[0].host}')/whoami"
```

And why not send test statements from Potsie's repository:

```bash
$ curl -sL \
    https://github.com/openfun/potsie/raw/main/fixtures/elasticsearch/lrs.json.gz | \
  gunzip | \
  head -n 100 | \
  jq -s . | \
  sed "s/@timestamp/timestamp/g" | \
  curl -sLk \
    --user foo:bar \
    -X POST \
    -H "Content-Type: application/json" \
    "https://$(\
        kubectl -n development-ralph \
        get \
        ingress/ralph-app-current \
        -o jsonpath='{.spec.rules[0].host}')/xAPI/statements/" \
    -d @-
```

> This example command requires [`jq`](https://stedolan.github.io/jq/) to
> serialize the request payload (xAPI statements). When dealing with JSON data,
> we strongly recommend installing it to manipulate them from the command line.

### Perform Arnold's operations

If you want to run the `bin/arnold` script to run specific Arnold commands, you
must ensure that your environment is properly set and that Arnold runs in
development mode (_i.e._ using the `-d` flag):

```bash
$ source .k3d-cluster.env.sh
$ bin/arnold -d -c ralph -e development -- vault -a ralph view
```

### Stop `k3d` cluster

When finished to work on the Tray, you can stop the `k3d` cluster using the `k3d-stop` helper:

```bash
$ make k3d-stop
```
