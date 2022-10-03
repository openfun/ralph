# k3d cluster environment for development purpose

echo -n "Loading k3d cluster environment... "

export ARNOLD_DEFAULT_VAULT_PASSWORD=arnold
export ANSIBLE_VAULT_PASSWORD="${ARNOLD_DEFAULT_VAULT_PASSWORD}"
export ARNOLD_IMAGE_TAG=master
export K3D_BIND_HOST_PORT_HTTP=80
export K3D_BIND_HOST_PORT_HTTPS=443
export K3D_CLUSTER_NAME=ralph
export K3D_ENABLE_REGISTRY=1
export K3D_REGISTRY_HOST=registry.127.0.0.1.nip.io
export K3D_REGISTRY_NAME=k3d-registry.127.0.0.1.nip.io
export K3D_REGISTRY_PORT=5000
export K8S_DOMAIN=$(hostname -I | awk '{print $1}')
export MINIMUM_AVAILABLE_RWX_VOLUME=3

echo "done."
