
# Forwarding to another LRS

Ralph LRS server can be configured to forward xAPI statements it receives to other LRSs.
Statement forwarding enables the [Total Learning Architecture](https://adlnet.gov/projects/tla/) and allows systems containing multiple LRS to share data.

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

!!! warning
    For a forwarding configuration to be valid it is required that all key/value pairs are defined.

Example of a valid forwarding configuration:

```bash title=".env"
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
