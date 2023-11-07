# LRS HTTP server

Ralph implements the Learning Record Store (LRS) [specification](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Communication.md#part-three-data-processing-validation-and-security) defined by [ADL](https://github.com/adlnet).

Ralph LRS, based on [FastAPI](https://fastapi.tiangolo.com/), has the following key features:

- Supports of multiple databases through different [backends](../tutorials/lrs/backends.md)
- Secured with multiple [authentication methods](../tutorials/lrs/authentication/index.md)
- Supports [multitenancy](../tutorials/lrs/multitenancy.md)
- Enables the Total Learning Architecture with [statements forwarding](../tutorials/lrs/forwarding.md)
- Monitored thanks to the [Sentry integration](../tutorials/lrs/sentry.md)


## API documentation

[OAD(./docs/features/openapi.json)]
