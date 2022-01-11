# API Server

Ralph comes with an API server that aims to implement the LRS specification (still a work in progress).

## Getting started

The API server can be started up with the following command:

```bash
$ ralph runserver
```

Before you can start your API server and make requests against it, you need to set up your credentials.

### Creating a credentials file

The credentials file is expected to be a valid JSON file. Its location is specified by the `RALPH_AUTH_FILE` configuration value. By default, `ralph` will look for the `auth.json` file in the application directory (see [click documentation for details](https://click.palletsprojects.com/en/8.0.x/api/#click.get_app_dir)).

The expected format is a list of entries (JSON objects) each containing the username, the user's `bcrypt` hashed+salted password and scopes they can access:

```json
[
  {
    "username": "john.doe@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["example_scope"]
  },
  {
    "username": "simon.says@example.com",
    "hash": "$2b$12$yBXrzIuRIk6yaft5KUgVFOIPv0PskCCh9PXmF2t7pno.qUZ5LK0D2",
    "scopes": ["second_scope", "third_scope"]
  }
]
```

The hash can be generated with a python script executed directly in the command line:

```bash
# Install bcrypt
$ python3 -m pip install bcrypt
# Generate the hash and print it to console
$ python3 -c 'import bcrypt; print(bcrypt.hashpw(b"PASSWORD", bcrypt.gensalt()).decode("ascii"))'
```

### Making a GET request

The first request that can be answered by the ralph API server is a `whoami` request, which checks if the user is authenticated and returns their username and permission scopes.

Use curl to get `http://localhost:8100/whoami`:

```bash
$ curl http://localhost:8100/whoami
< HTTP/1.1 400 Bad Request
< {"error":"Missing authentication credentials."}
```

Send your username and password to the API server through HTTP Basic Auth:

```bash
$ curl --user john.doe@example.com:PASSWORD http://localhost:8100/whoami
< HTTP/1.1 200 OK
< {"username":"john.doe@example.com","scopes":["authenticated","example_scope"]}
```
