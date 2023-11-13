# Deploy Ralph LRS to Kubernetes using Helm

This tutorial aims at deploying Ralph LRS running over Kubernetes using Helm. In this tutorial, you will learn to:

- run a small Kubernetes cluster on your machine,
- deploy applications to this cluster using Helm,
- submit learning traces to a LRS (Learning Record Store),

## Requirements

- [`curl`](https://curl.se/), the CLI to make HTTP requests.
- [`jq`](https://stedolan.github.io/jq/), the JSON data Swiss-Knife.
- [`k3d`](https://k3d.io), a lightweight kubernetes distribution to work locally on the project.
- [`kubectl`](https://kubernetes.io/docs/tasks/tools/#kubectl), the Kubernetes CLI.
- [`helm`](https://helm.sh/), the package manager for Kubernetes.

## Create a local kubernetes cluster

!!! info
    If you already have a fully fonctional Kubernetes cluster to work with,
    you can use it and proceed to the next section after having created the
    `development-ralph` namespace.

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

Check that we can see the `k3d` context with `kubectl`:
```
kubectl config get-contexts
```

This command should print the following output:
```
CURRENT   NAME        CLUSTER     AUTHINFO          NAMESPACE
*         k3d-ralph   k3d-ralph   admin@k3d-ralph
```

!!! tip

    If you don't see it in the list of contexts, you probably already use `kubectl` to manage other clusters.
    You need to create and use a specific config for `k3d` as so:

    ```
    export KUBECONFIG=$(k3d kubeconfig write ralph)
    ```
    
    Don't forget to unset the variable when you want to manage other clusters back! (or just, you know, kill the terminal 👀)


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

The proposed lightweight learning analytics stack is composed of two different
applications:

1. [Elasticsearch](https://www.elastic.co/elasticsearch/), the data lake that will store learning traces (xAPI),
2. [Ralph](https://github.com/openfun/ralph), our lightweight LRS,

### Elasticsearch

In its recent releases, Elastic recommends to deploy its services using Custom Resource Definitions (CRDs) installed via its official Helm chart.
Let's install it:

```sh
# Add the offical Elasticsearch Helm repository
helm repo add elastic https://helm.elastic.co

# Update the list of available charts
helm repo update

# Install the eck operator
helm install elastic-operator elastic/eck-operator
```

Now we need to specify what we want the operator to deploy. Let's create a `manifest/data-lake.yaml` file with the following content:

```yaml title="manifest/data-lake.yaml"

apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: data-lake
spec:
  version: 8.8.1
  nodeSets:
    - name: default
      count: 2
      config:
        node.store.allow_mmap: false
      podTemplate:
        spec:
          containers:
          - name: elasticsearch
            env:
              - name: ES_JAVA_OPTS
                value: -Xms512m -Xmx512m
            resources:
              requests:
                memory: 512Mi
                cpu: 0.5
              limits:
                memory: 2Gi
                cpu: 2

```

Let's deploy a two-nodes elasticsearch "cluster":

```sh
kubectl apply -f manifest/data-lake.yaml
```

Once applied, your elasticsearch pods should be running. You can check pods status by using the following command:

```sh
kubectl get pods -w
```

We expect to see two pods called `data-lake-es-default-0` and `data-lake-es-default-1`.

When our Elasticsearch cluster is up (this can take few minutes), you may create the Elasticsearch index that will be used to store learning traces (xAPI statements):

```sh
# Store elastic user password
export ELASTIC_PASSWORD="$(kubectl get secret data-lake-es-elastic-user -o jsonpath="{.data.elastic}" | base64 -d)"

# Execute an index creation request in the elasticsearch container
kubectl exec data-lake-es-default-0 --container elasticsearch -- \
    curl -ks -X PUT "https://elastic:${ELASTIC_PASSWORD}@localhost:9200/statements?pretty"
```

!!! warning
    In a production environment, we recommend to create a user with appropriate
    roles and permissions depending on your application needs and use its
    credentials.

Our data lake is now ready! Let's deploy Ralph LRS.

### Ralph LRS

Ralph LRS is distributed as a Helm chart in the DockerHub OCI [openfuncharts](https://hub.docker.com/r/openfuncharts).

First, create a `dev-values.yaml` file and add with the following:

```yaml title="dev-values.yaml"
envSecrets:
  RALPH_BACKENDS__DATA__ES__INDEX: statements
  RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__ca_certs: "/usr/local/share/ca-certificates/ca.crt"
  RALPH_BACKENDS__DATA__ES__CLIENT_OPTIONS__verify_certs: "true"

lrs:
  auth:
    - username: "admin"
      hash: "$2b$12$JFK.YCdbUWD2rS94fT4.m.KC/fIMzUMPMtjaD4t3t1iAfqki3ZPOq"
      scopes: ["example_scope"]

elastic:
  enabled: true
  mountCACert: true
  caSecretName: "data-lake-es-http-certs-public"
```

!!! tip

    All the default values of Ralph Helm chart can be fetched with:

    ```sh
    helm show values oci://registry-1.docker.io/openfuncharts/ralph --version 0.3.0
    ```

Now we can install Ralph LRS with this single line:
```
helm install \
  --values dev-values.yaml \
  --set envSecrets.RALPH_BACKENDS__DATA__ES__HOSTS=https://elastic:"${ELASTIC_PASSWORD}"@data-lake-es-http:9200 \
  lrs oci://registry-1.docker.io/openfuncharts/ralph \
  --version 0.3.0
```
!!! tip
    You are now familiar with the procedure: you can check Ralph deployment using the `kubectl get pods -w` and `kubectl get svc -w lrs-ralph` commands.

As the Ralph LRS is not exposed, we will create a bridge from our machine to the Ralph LRS cluster using the `kubectl port-forward` command:

```
kubectl port-forward svc/lrs-ralph 8080
```

The command waits until it is stopped using <kbd>CTRL+C</kbd> kill signal.
To test our deployment, in another terminal, let's send 100 example statements to the LRS:

```sh
curl -sL https://github.com/openfun/potsie/raw/main/fixtures/elasticsearch/lrs.json.gz | \
  gunzip | \
  head -n 100 | \
  jq -s . | \
  sed "s/@timestamp/timestamp/g" | \
  curl -L \
    --user admin:password \
    -X POST \
    -H "Content-Type: application/json" \
    http://localhost:8080/xAPI/statements/ -d @-
```

If everything went well, the LRS should respond with 100 UUIDs filling our terminal.
Let's check what our statements look like by querying them to the LRS:

```sh
# Fetch stored statements
curl -L --user admin:password http://localhost:8080/xAPI/statements/ | \
  jq
```

!!! tip
    You may choose to click on the LRS URL link from your terminal to open it with your default web browser. HTTP Basic Auth credentials are `admin` for the login and `password` for the password.

Congrats, you did it! 🎉

You can stop and delete the k3d cluster with:
```sh
k3d cluster stop ralph
k3d cluster delete ralph
```

## Go further 

If you want to deploy a complete learning analytics stack, check this great tutorial at [https://github.com/openfun/k8s-la-stack-tutorial/]() that deploys on a real Kubernetes cluster:

- Ralph LRS;
- Elasticsearch datalake;
- Superset dashboard system.
