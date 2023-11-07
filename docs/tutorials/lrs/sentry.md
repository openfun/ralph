
# Sentry

Ralph provides Sentry integration to monitor its LRS server and its CLI.
To activate Sentry integration, one should define the following environment variables:

```bash title=".env"
RALPH_SENTRY_DSN={PROTOCOL}://{PUBLIC_KEY}:{SECRET_KEY}@{HOST}{PATH}/{PROJECT_ID}
RALPH_EXECUTION_ENVIRONMENT=development
```

The Sentry DSN (Data Source Name) can be found in your project settings from the Sentry application. The execution environment should reflect the environment Ralph has been deployed in (_e.g._ `production`).

You may also want to [monitor the performance](https://develop.sentry.dev/sdk/performance/) of Ralph by configuring the CLI and LRS traces sample rates:

```bash title=".env"
RALPH_SENTRY_CLI_TRACES_SAMPLE_RATE=0.1
RALPH_SENTRY_LRS_TRACES_SAMPLE_RATE=0.3
```
!!! info "Sample rate"
    
    A sample rate of `1.0` means 100% of transactions are sent to sentry and `0.1` only 10%.

If you want to lower noisy transactions (_e.g._ in a Kubernetes cluster), you can disable health checks related ones:

```bash title=".env"
RALPH_SENTRY_IGNORE_HEALTH_CHECKS=True
```
