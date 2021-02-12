# Contribute

## Ralph's core

To start playing with `ralph`, you should build it using the `bootstrap` Make target:

```
$ make bootstrap
```

Once the project has been bootstrapped, you may want to edit generated `.env`
file to set up available backends parameters that will be injected in the
running container as environmnet variables to configure Ralph (see [backends
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

# Run pylint
$ make lint-pylint

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
```

### Working with local backends

Not all backends are accessible in a local environment development; for now
only `elasticsearch` and `swift` services are accessible as docker containers
(see `docker-compose.yml` services).

To configure those backends, we provide default parameters in the `.env.dist`
template, you can copy/paste them in your `.env` file (and uncomment them so
that they are properly injected in running containers).

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
it's time to play with those:

```bash
# Store a JSON file in the Swift backend
$ echo '{"id": 1, "foo": "bar"}' | \
    ./bin/ralph push -b swift -f foo.json

# Check that we have created a new JSON file in the Swift backend
$ bin/ralph list -b swift
foo.json

# Fetch the content of the JSON file and index it in Elasticsearch
$ bin/ralph fetch -b swift foo.json | \
    bin/ralph push -b es

# Check that we have properly indexed the JSON file in Elasticsearch
$ bin/ralph fetch -b es
{"id": 1, "foo": "bar"}
```

## Ralph's tray

Ralph is distributed along with its tray (a deployable package for Kubernetes
clusters using [Arnold](https://github.com/openfun/arnold)). If you intend to
work on this tray, please refer to Arnold's documentation.
