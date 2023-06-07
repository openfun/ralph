# API Server

Ralph comes with an API server that aims to implement the Learning Record Store
(LRS) specification (still a work in progress).

## Getting started

The API server can be started up with the following command:

```bash
$ ralph runserver --backend es
```

The `--backend` (or `-b`) option specifies which database backend to use for
LRS data storage and retrieval. See Ralph's [backends
documentation](./backends.md) for more details.

However, before you can start your API server and make requests against it, you
need to set up your credentials.

### Creating a credentials file

The credentials file is expected to be a valid JSON file. Its location is
specified by the `RALPH_AUTH_FILE` configuration value. By default, `ralph`
will look for the `auth.json` file in the application directory (see [click
documentation for
details](https://click.palletsprojects.com/en/8.1.x/api/#click.get_app_dir)).

The expected format is a list of entries (JSON objects) each containing the
username, the user's `bcrypt` hashed+salted password, scopes they can
access, and an `agent` object used to represent the user in the LRS. The 
`agent` is constrained by [LRS specifications](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#description-2), and must use one of four valid 
[Inverse Functional Identifiers](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#inversefunctional).

```json
[
  {
    "username": "john.doe@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["example_scope"],
    "agent": {
      "mbox": "mailto:john.doe@example.com"
    }
  },
  {
    "username": "simon.says@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["second_scope", "third_scope"],
    "agent": {
      "account": {
        "name": "simonsAccountName",
        "homePage": "http://www.exampleHomePage.com"
      }
    }
  }
]
```

To create a new user credentials, Ralph's CLI provides a dedicated command:

```bash
$ ralph auth \
    --username janedoe \
    --password supersecret \
    --scope janedoe_scope \
    --agent-mbox mailto:janedoe@example.com \
    # or --agent-mbox-sha1sum ebd31e95054c018b10727ccffd2ef2ec3a016ee9\
    # or --agent-openid "http://jane.openid.example.org/" \
    # or --agent-account-name exampleAccountname \
    #    --agent-account-homePage http://www.exampleHomePage.com \
    -w
```

This command updates your credentials file with the new `janedoe` user.

> Note that running this command requires that you installed Ralph with the CLI
> optional dependencies, _e.g._ `pip install ralph-malph[cli]` (which we highly
> recommend).

### Making a GET request

The first request that can be answered by the ralph API server is a `whoami` request, which checks if the user is authenticated and returns their username and permission scopes.

Use curl to get `http://localhost:8100/whoami`:

```bash
$ curl http://localhost:8100/whoami
< HTTP/1.1 401 Unauthorized
< {"error":"Not authenticated"}
```

Send your username and password to the API server through HTTP Basic Auth:

```bash
$ curl --user john.doe@example.com:PASSWORD http://localhost:8100/whoami
< HTTP/1.1 200 OK
< {"scopes":["example_scope"], "agent": {"mbox": "mailto:john.doe@example.com"}}
```

### Forwarding statements

Ralph's API server can be configured to forward xAPI statements it receives to other
LRSes.

To configure statement forwarding, you need to create a `.env` file in the current
directory and define the `RALPH_XAPI_FORWARDINGS` variable or define the
`RALPH_XAPI_FORWARDINGS` environment variable.

The value of the `RALPH_XAPI_FORWARDINGS` variable should be a JSON encoded list of
dictionaries where each dictionary defines a forwarding configuration and consists of
the following key/value pairs:

| key              | value type | description                                                                   |
|:-----------------|:-----------|:------------------------------------------------------------------------------|
| `is_active`      | `boolean`  | Specifies whether or not this forwarding configuration should take effect.    |
| `url`            | `URL`      | Specifies the endpoint URL where forwarded statements should be send.         |
| `basic_username` | `string`   | Specifies the basic auth username.                                            |
| `basic_password` | `string`   | Specifies the basic auth password.                                            |
| `max_retries`    | `number`   | Specifies the number of times a failed forwarding request should be retried.  |
| `timeout`        | `number`   | Specifies the duration in seconds of network inactivity leading to a timeout. |

> Note that for a forwarding configuration to be valid it is required that all key/value
> pairs are defined.

Example of a valid forwarding configuration:

```bash
RALPH_XAPI_FORWARDINGS='
[
  {
    "is_active": true,
    "url": "http://lrs1.example.com/xAPI/statements/",
    "basic_username": "admin1@example.com",
    "basic_password": "PASSWORD1",
    "max_retries": 1,
    "timeout": 5
  },
  {
    "is_active": true,
    "url": "http://lrs2.example.com/xAPI/statements/",
    "basic_username": "admin2@example.com",
    "basic_password": "PASSWORD2",
    "max_retries": 5,
    "timeout": 0.2
  }
]
'
```

### Sentry configuration

Ralph provides Sentry integration to monitor its LRS server and its CLI.
To activate Sentry integration, one should define the following environment variables:

```bash
RALPH_SENTRY_DSN={PROTOCOL}://{PUBLIC_KEY}:{SECRET_KEY}@{HOST}{PATH}/{PROJECT_ID}
RALPH_EXECUTION_ENVIRONMENT=development
```

The Sentry DSN (Data Source Name) can be found in your project settings from Sentry application. The execution environment should reflect the environment Ralph has been deployed in (_e.g._ `production`).

You may also want to [monitor the performance](https://develop.sentry.dev/sdk/performance/) of Ralph by configuring the CLI and LRS traces sample rates:
```bash
RALPH_SENTRY_CLI_TRACES_SAMPLE_RATE=0.1
RALPH_SENTRY_LRS_TRACES_SAMPLE_RATE=0.3
```
> Note that a sampling rate of `1.0` means 100% of transactions are sent to sentry and `0.1` only 10%.

If you want to lower noisy transactions (_e.g._ in a Kubernetes cluster), you can disable health checks related ones:
```bash
RALPH_SENTRY_IGNORE_HEALTH_CHECKS=True
```