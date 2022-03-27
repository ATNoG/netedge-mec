
# Kubernetes installation (just master node)

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
## Install container runtime (in this case containerd)
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

## Initialize master node
```bash
## verify if true
lsmod | grep br_netfilter         

# Enable Kubelet service
sudo systemctl enable kubelet

# Pull for control plane
sudo kubeadm config images pull

# Define dns name
echo 127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4 controller | sudo tee -a /etc/hosts
echo ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 controller | sudo tee -a /etc/hosts
sudo hostnamectl set-hostname controller

# create the cluster
$ sudo kubeadm init \
  --pod-network-cidr=192.168.0.0/16 \
  --upload-certs \
  --control-plane-endpoint=controller

# configure kubectl
$ mkdir -p $HOME/.kube
$ sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
$ sudo chown $(id -u):$(id -g) $HOME/.kube/config

# install network plugin (in this case we are using Calico)
$ kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml 
$ kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml
```

## Check controller status
```bash
# Check running pods
watch kubectl get pods --all-namespaces
# Check node status and roles
kubectl get nodes
```

## Install bash-completion ([bash auto-completion on Linux](https://kubernetes.io/docs/tasks/tools/included/optional-kubectl-configs-bash-linux/)):
```bash
$ sudo apt-get install bash-completion
$ echo 'source /usr/share/bash-completion/bash_completion' >> ~/.bashrc
```