
# Authentication

The API server supports the following authentication methods:

- [HTTP basic authentication](basic.md)
- [OpenID Connect authentication](oidc.md) on top of OAuth2.0

Either one or both can be enabled for Ralph LRS using the environment variable `RALPH_RUNSERVER_AUTH_BACKENDS`:

```bash
RALPH_RUNSERVER_AUTH_BACKENDS=basic,oidc
```
