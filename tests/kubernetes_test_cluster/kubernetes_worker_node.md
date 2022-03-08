
# Kubernetes installation - Master and Worker Nodes

From the article [Install Kubernetes Cluster on Ubuntu 20.04 with kubeadm](https://computingforgeeks.com/deploy-kubernetes-cluster-on-ubuntu-with-kubeadm/):

## Update system and reboot
 
```bash
sudo apt update
sudo apt -y upgrade && sudo systemctl reboot
```
## Install kubelet, kubeadm, kubectl
```bash
# Add kubernetes repositories for ubuntu 20.04 
sudo apt update
sudo apt -y install curl apt-transport-https
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install required packages
sudo apt update
sudo apt -y install vim git curl wget kubelet=1.22.7-00 kubeadm=1.22.7-00 kubectl=1.22.7-00
sudo apt-mark hold kubelet kubeadm kubectl
```

## Change settings to work with kubernetes
```bash
# Disable swap
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
sudo swapoff -a
# Enable kernel modules
sudo modprobe overlay
sudo modprobe br_netfilter

# Add settings to sysctl
sudo tee /etc/sysctl.d/kubernetes.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

# Reload sysctl
sudo sysctl --system
```
- Install container runtime (in this case containerd)
```bash
# Configure persistent loading of modules
sudo tee /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF

# Load at runtime
sudo modprobe overlay
sudo modprobe br_netfilter

# Ensure sysctl params are set
sudo tee /etc/sysctl.d/kubernetes.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

# Reload configurations
sudo sysctl --system

# Install required packages
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates

# Add Docker repo
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install containerd
sudo apt update
sudo apt install -y containerd.io

# Configure containerd and start service
sudo mkdir -p /etc/containerd
sudo containerd config default>/etc/containerd/config.toml

# restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
systemctl status  containerd
```

## Add master to known hosts
```bash
# Only required if endpoint address is not in DNS
echo <master_ip> <endpoint> | sudo tee -a /etc/hosts
```
## Add nodes to the cluster
```bash
# Token Option 1 - Mostly used when generating the cluster
# Using the token and command obtained from the kubeadm init command (using an already generated token)


# Token Option 2 - To add nodes after some time has passed since cluster creation

# Obtain API Server Advertise Address 
# Command to be run on the master node
kubectl cluster-info

# Get Discovery token CA cert hash
# Required for token-based discovery since the join command validates the root CA public key
# Command to be run on the master node
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'

# Check if there are any valid tokens by listing existing kubeadm tokens
kubeadm tokens list

# If there is no token available generate a new token
# Command to be run on master
kubeadm token create --print-join-command


# Adding a node to cluster
# Command to be run on node
kubeadm join <endpoint>:<endpoint_port> \
 --token <token>
 --discovery-token-ca-cert-hash <hash_type>:<token_hash>
```
## Adding an extra master 
```bash
kubeadm join <endpoint>:<endpoint_port> \
 --token <token>
 --discovery-token-ca-cert-hash <hash_type>:<token_hash>
 --control-plane
```

## Checking cluster
```bash
# Check nodes - Should have as many worker and master nodes as kubeadm join commands 
kubectl get nodes 
```

## Install bash-completion ([bash auto-completion on Linux](https://kubernetes.io/docs/tasks/tools/included/optional-kubectl-configs-bash-linux/)):
```bash
$ sudo apt-get install bash-completion
$ echo 'source /usr/share/bash-completion/bash_completion' >> ~/.bashrc
```