# Ralph Helm Chart

This is the helm chart used to deploy ralph application.

All default values are in `values.yaml`.

⚠️  This helm chart is still under active development and is not suitable for production use.

## Review manifest

To generate and review your manifest, under `./src/helm` run the following command:
```
$ helm template .
```

## Deploy chart
### Requirements
* Helm
* Needed Kubernetes context selected


### Environments

Please note that with Helm, you can extend the values files. There is no need to copy/paste all the default values and you can replace a value by setting it in your env file.

You can add an environment values file under the root of the chart, _e.g._ `dev-values.yaml` and set only needed customizations.


This chart use the file `vaul.yaml` to set the mandatory secrets for the application

### How to

Under `./src/helm`

```
$ helm upgrade --install RELEASE_NAME ralph/. --values ralph/dev-values.yaml
```

Tips:

* use `--values` to pass an env values file to extend and/or replace the default values
* `--set var=value` to replace one var/value
* `--dry-run` to verify your manifest before deploying
