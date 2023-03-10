# Deploy a learning analytics stack to Kubernetes in minutes using Helm

This tutorial aims at deploying a complete Learning Analytics stack running over
Kubernetes using Helm. In this tutorial, you will learn to:

- run a small Kubernetes cluster on your machine,
- deploy application to this cluster using Helm,
- submit learning traces to a LRS (Learning Record Store),
- analyze learning traces _via_ Grafana dashboards.

## Requirements

- [`curl`](https://curl.se/), the CLI to make HTTP requests.
- [`jq`](https://stedolan.github.io/jq/), the JSON data Swiss-Knife.
- [`k3d`](https://k3d.io), a lighweight kubernetes distribution to work locally on the project.
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/#kubectl), the Kubernetes CLI.
- [`helm`](https://helm.sh/), the package manager for Kubernetes.

## Create a local kubernetes cluster

> 🤚 If you already have a fully fonctional Kubernetes cluster to work with,
> you can use it and proceed to the next section after have created the
> `development-ralph` namespace.

Thanks to K3D, creating a local, docker-based Kubernetes cluster can be
achieved using the following command:

```sh
k3d cluster create ralph
```

This cluster is called `ralph`, you can check that it has been created using:

```
k3d cluster list
```

This command should print the following output (note that the cluster is up and
running):

```
NAME     SERVERS   AGENTS   LOADBALANCER
ralph    1/1       0/0      true
```

We will now create a new namespace to work on:

```sh
kubectl create namespace development-ralph
```

And we will set this namespace as the default namespace for future `kubectl`
commands:

```sh
kubectl config set-context --current --namespace=development-ralph
```

Our cluster is now ready to host our learning analytics stack!

## Deploy a learning analytics stack

The proposed learning analytics stack is composed of three different
applications:

1. [Ralph](https://github.com/openfun/ralph), a lightweight LRS,
2. [Elasticsearch](https://www.elastic.co/elasticsearch/), our data lake that will store learning traces (xAPI),
3. [Grafana](https://grafana.com/grafana/), a dashboarding solution.

### Elasticsearch

As Elasticsearch is required by Ralph and Grafana, we will deploy an
Elasticsearch cluster using the official elasticsearch Helm Chart:

```sh
# Add the offical Elasticsearch Helm repository
helm repo add elastic https://helm.elastic.co

# Update the list of available charts
helm repo update

# Deploy a "simple" Elasticsearch cluster with 3 nodes
helm install \
  es-quickstart \
  elastic/elasticsearch \
  -n development-ralph \
  --set antiAffinity=soft
```

> By default, this Helm chart will deploy three (3) Elasticsearch nodes in
> three (3) differents Kubernetes nodes. Since we only have a single-node
> Kubernetes cluster, we set the `antiAffinity` value to `soft` to allow our
> deployment scenario. Feel free to adapt this option value depending on your
> cluster constraints.

Once installed, you can check pods status using the following command (and wait
for them to get ready):

```sh
kubectl get pods -l app=elasticsearch-master -w
```

Once the Elasticsearch cluster is up and running, we will need to get
automatically generated credentials to connect other applications to the
service.

For this tutorial, we will fetch `elastic` user's password using the following
command:

```sh
kubectl get secrets \
  elasticsearch-master-credentials \
  -ojsonpath='{.data.password}' | \
    base64 -d
```

> In a production environment, we recommend to create a user with appropriate
> roles and permissions depending on your application needs and use its
> credentials.

To secure Elasticsearch cluster nodes communication, during its deployment, the
Helm chart created a self-generated root certificate used to sign Elasticsearch
cluster node SSL certificates. We will need to provide this certificate to our
applications that connect to the cluster. It can be fetched using:

```sh
kubectl get secrets elasticsearch-master-certs -ojson | \
  jq -r ".data.\"ca.crt\"" | \
  base64 -d
```

The final step of the Elasticsearch cluster preparation is to create an index
to store our xAPI statements. As the Elasticsearch service is not exposed, we
will create a bridge from our machine to the Elasticsearch cluster using the
`kubectl port-forward` command:

```sh
kubectl port-forward svc/elasticsearch-master 9200
```

The command waits until it is stop using <kbd>CTRL+C</kbd> kill signal, so we
will need to create the `statements` index from another terminal using Curl:

```
curl -k -X PUT https://elastic:<PASTE PASSWORD HERE>@localhost:9200/statements
```

> You need to substitute the `<PASTE PASSWORD HERE>` placeholder with the
> `elastic` user password we've fetched previously.

> Note that our request target the `localhost` server name, since all traffic
> on port 9200 is forwarded to the Elasticsearch service running in our
> Kubernetes cluster.

### Ralph

As long as Ralph Helm chart is not published in a public repository,
one will need to clone Ralph's project first.

Next step is to add a new user to be able to log in the LRS server. 
Create credentials for a new user with the following command:

```sh
docker run --rm fundocker/ralph:3.5.0 ralph auth \
    --username janedoe \
    --password supersecret \
    --scope janedoe_scope
```

Edit Ralph's vault (src/helm/ralph/vault.yml) to define the following values:

```yaml
# Elasticsearch cluster connection URL
RALPH_BACKENDS__DATABASE__ES__HOSTS: https://elastic:<PASTE PASSWORD HERE>@elasticsearch-master:9200

# Elasticsearch cluster nodes CA certificate
ES_CA_CERTIFICATE: |
  -----BEGIN CERTIFICATE-----
  <PASTE CERTIFICATE HERE>
  -----END CERTIFICATE-----

# LRS client credentials
LRS_AUTH:
  - username: "janedoe"
    hash: "<PASTE HASH HERE>"
    scopes:
      - "janedoe_scope"
```

Edit your `dev-values.yml` (default Helm chart values override).

```
cd src/helm
helm install ralph-lrs ralph/ \
  -n development-ralph \
  -f dev-values.yaml \
  --set ralph_lrs.host="ralph.$(hostname -I | awk '{print $1}').nip.io"
```

**FIXME** review ingress usage in a local k8s cluster and prefer using the following:

```
kubectl port-forward svc/ralph-app-traefik 8080
```

Send one hundred (100) example statements to the LRS:

```sh
curl -sL https://github.com/openfun/potsie/raw/main/fixtures/elasticsearch/lrs.json.gz | \
  gunzip | \
  head -n 100 | \
  jq -s . | \
  curl -Lk \
    --user johndoe:password \
    -X POST \
    -H "Content-Type: application/json" \
    http://localhost:8080/xAPI/statements/ -d @-
```

And fetch them back:

```sh
curl -Lk --user johndoe:password http://localhost:8080/xAPI/statements/ | \
  jq
```

### Apache Superset

TODO.
