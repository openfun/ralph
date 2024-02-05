# Ralph Helm chart

Ralph LRS is distributed as a [Helm](https://helm.sh/) chart in the DockerHub OCI
[openfuncharts](https://hub.docker.com/r/openfuncharts).

## Setting environment values

All default values are in the `values.yaml` file. With Helm, you can extend the values
file: there is no need to copy/paste all the default values. You can create an
environment values file, _e.g._ `custom-values.yaml` and only set needed customizations.

All sensitive environment values, needed for Ralph to work, are expected to be in an
external Secret Kubernetes object. An example manifest is provided in the
`ralph-env-secret.yaml` file
[here](https://github.com/openfun/ralph/blob/main/src/helm/manifests/ralph-env-secret.yaml)
that you can adapt to fit your needs.

All other non-sensitive environment values, also needed for Ralph to work, are expected
to be in an external ConfigMap Kubernetes object. An example manifest is provided in the
`ralph-env-cm.yaml` file
[here](https://github.com/openfun/ralph/blob/main/src/helm/manifests/ralph-env-cm.yaml)
that you can adapt to fit your needs.

## Creating authentication secret

Ralph stores users credentials in an external Secret Kubernetes object. An example
authentication file `auth-demo.json` is provided
[here](https://github.com/openfun/ralph/blob/main/src/helm/manifests/auth-demo.json),
that you can take inspiration from. Refer to the LRS guide for [creating user
credentials](https://openfun.github.io/ralph/latest/tutorials/lrs/authentication/basic/#creating_user_credentials).

## Reviewing manifest

To generate and review your Helm generated manifest, under `./src/helm` run the
following command:

```bash
helm template oci://registry-1.docker.io/openfuncharts/ralph
```

## Installing the chart

Ralph Helm chart is distributed on DockerHub, and you can install it with:
```bash
helm install RELEASE_NAME oci://registry-1.docker.io/openfuncharts/ralph
```

Tips:

* use `--values` to pass an env values file to extend and/or replace the default values
* `--set var=value` to replace one var/value
* `--dry-run` to verify your manifest before deploying


## Tutorial: deploying Ralph LRS on a local cluster

This tutorial aims at deploying Ralph LRS on a local Kubernetes cluster using Helm. In
this tutorial, you will learn to:

- run and configure a small Kubernetes cluster on your machine,
- deploy a data lake that stores learning records: we choose Elasticsearch,
- deploy Ralph LRS (Learning Records Store) that receives and sends learning records in
  xAPI,

### Requirements

- [`curl`](https://curl.se/), the CLI to make HTTP requests.
- [`jq`](https://stedolan.github.io/jq/), the JSON data Swiss-Knife.
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/#kubectl), the Kubernetes CLI.
- [`helm`](https://helm.sh/), the package manager for Kubernetes.
- [`minikube`](https://minikube.sigs.k8s.io/docs/start/), a lightweight kubernetes
  distribution to work locally on the project.

### Bootstrapping a local cluster

Let's begin by running a local cluster with Minikube, where we will deploy Ralph on.

```bash
# Start a local kubernetes cluster
minikube start
```

We will now create our own Kubernetes namespace to work on:

```bash
# This is our namespace
export K8S_NAMESPACE="learning-analytics"

# Check your namespace value
echo ${K8S_NAMESPACE}

# Create the namespace
kubectl create namespace ${K8S_NAMESPACE}

# Activate the namespace
kubectl config set-context --current --namespace=${K8S_NAMESPACE}
```

### Deploying the data lake: Elasticsearch

In its recent releases, Elastic recommends deploying its services using Custom Resource
Definitions (CRDs) installed via its official Helm chart. We will first install the
Elasticsearch (ECK) operator cluster-wide:

```bash
# Add elastic official helm charts repository
helm repo add elastic https://helm.elastic.co

# Update available charts list
helm repo update

# Install the ECK operator
helm install elastic-operator elastic/eck-operator -n elastic-system --create-namespace
```

Now that CRDs are already deployed cluster-wide, we can deploy an Elasticsearch cluster.
To help you in this task, we provide an example manifest `data-lake.yml`, that deploy a
two-nodes elasticsearch "cluster". Adapt it to match your needs, then apply it with:

```bash
kubectl apply -f data-lake.yml
```

Once applied, your elasticsearch pod should be running. You can check this using the
following command:

```bash
kubectl get pods -w
```

We expect to see two pods called `data-lake-es-default-0` and `data-lake-es-default-1`.

When our Elasticsearch cluster is up (this can take few minutes), you may create the
Elasticsearch index that will be used to store learning traces (xAPI statements):

```bash
# Store elastic user password
export ELASTIC_PASSWORD="$(kubectl get secret data-lake-es-elastic-user -o jsonpath="{.data.elastic}" | base64 -d)"

# Execute an index creation request in the elasticsearch container
kubectl exec data-lake-es-default-0 --container elasticsearch -- \
    curl -ks -X PUT "https://elastic:${ELASTIC_PASSWORD}@localhost:9200/statements?pretty"
```

Our Elasticsearch cluster is all set. In the next section, we will now deploy Ralph, our
LRS.

### Deploy the LRS: Ralph

First and foremost, we should create a Secret object containing the user credentials
file. We provide an example authentication file
[`auth-demo.json`](https://github.com/openfun/ralph/blob/main/src/helm/manifests/auth-demo.json)
that you can take inspiration from. We can create a secret object directly from the file
with the command:

```bash
kubectl create secret generic ralph-auth-secret \
    --from-file=auth.json=auth-demo.json
```

Secondly, we should create two objects containing environment values necessary for Ralph:

- a Secret containing sensitive environment variables such as passwords, tokens etc;
- a ConfigMap containing all other non-sensitive environment variables.

We provide two example manifests
([`ralph-env-secret.yaml`](https://github.com/openfun/ralph/blob/main/src/helm/manifests/ralph-env-secret.yaml)
and
[`ralph-env-cm.yml`](https://github.com/openfun/ralph/blob/main/src/helm/manifests/ralph-env-cm.yaml))
that you can adapt to fit your needs. 

For this tutorial, we only need to replace the `<PASSWORD>` tag in the Secret manifest
by the actual password of the `elastic` user with the command:
```bash
sed -i -e "s|<PASSWORD>|$ELASTIC_PASSWORD|g" ralph-env-secret.yaml
```

We can now apply both manifests, to create a ConfigMap and a Secret object in our local
cluster:
```bash
# Create Secret object
kubectl apply -f ralph-env-secret.yaml

# Create ConfigMap object
kubectl apply -f ralph-env-cm.yaml
```

We can now deploy Ralph:
```bash
helm install lrs oci://registry-1.docker.io/openfuncharts/ralph \
  --values development.yaml
```

One can check if the server is running by opening a network tunnel to the service using
the `port-forward` sub-command:

```bash
kubectl port-forward svc/lrs-ralph 8080:8080
```

And then send a request to the server using this tunnel:

```bash
curl --user admin:password localhost:8080/whoami
```

We expect a valid JSON response stating about the user you are using for this request.

If everything went well, we can send 22k xAPI statements to the LRS using:

```bash
gunzip -c ../../data/statements.jsonl.gz | \
  sed "s/@timestamp/timestamp/g" | \
  jq -s . | \
  curl -Lk \
    --user admin:password \
    -X POST \
    -H "Content-Type: application/json" \
    http://localhost:8080/xAPI/statements/ -d @-
```

Congrats 🎉

### Go further

Now that the LRS is running, we can go further and deploy the dashboard suite Warren.
Refer to the
[tutorial](https://github.com/openfun/warren/tree/main/src/helm#deploy-the-dashboard-suite-warren)
of the Warren Helm chart.

