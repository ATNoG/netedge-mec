
## Kubernetes installation (just master node)

 - From the article [Install Kubernetes Cluster on Ubuntu 20.04 with kubeadm](https://computingforgeeks.com/deploy-kubernetes-cluster-on-ubuntu-with-kubeadm/):
    ```bash
    $ sudo apt update
    $ sudo apt -y upgrade && sudo systemctl reboot
    
    # install kubenlet, kubeadm and kubectl
    $ sudo apt update
    $ sudo apt -y install curl apt-transport-https
    $ curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    $ echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
    
    $ sudo apt update
    $ sudo apt -y install vim git curl wget kubelet=1.22.7-00 kubeadm=1.22.7-00 kubectl=1.22.7-00
    $ sudo apt-mark hold kubelet kubeadm kubectl
    
    
    # disable swap
    $ sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    $ sudo swapoff -a
    
    $ sudo modprobe overlay
    $ sudo modprobe br_netfilter
    $ sudo tee /etc/sysctl.d/kubernetes.conf<<EOF
    net.bridge.bridge-nf-call-ip6tables = 1
    net.bridge.bridge-nf-call-iptables = 1
    net.ipv4.ip_forward = 1
    EOF
    $ sudo sysctl --system
    
    # install Docker runtime (other containers runtime are allowed)
    $ sudo apt update
    $ sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
    $ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    $ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    $ sudo apt update
    $ sudo apt install -y containerd.io docker-ce docker-ce-cli
    
    $ sudo mkdir -p /etc/systemd/system/docker.service.d
    
    $ sudo tee /etc/docker/daemon.json <<EOF
    {
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m"
      },
      "storage-driver": "overlay2"
    }
    EOF
    
    $ sudo systemctl daemon-reload 
    $ sudo systemctl enable --now docker
    
    # initialize master node
    $ lsmod | grep br_netfilter         # verify if true
    
    $ sudo systemctl enable --now kubelet
    
    $ sudo kubeadm config images pull
    
    # define dns name
    $ echo 127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4 controller | sudo tee -a /etc/hosts
    $ echo ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 controller | sudo tee -a /etc/hosts
    $ sudo hostnamectl set-hostname controller
    
    # create the cluster
    $ sudo kubeadm init \
      --pod-network-cidr=192.168.0.0/16 \
      --upload-certs \
      --control-plane-endpoint=controller
    
    # configure kubectl
    $ mkdir -p $HOME/.kube
    $ sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
    $ sudo chown $(id -u):$(id -g) $HOME/.kube/config
    
    # install network plugin (Calico)
    $ kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml 
    $ kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml
    ```

 - To check the pods instantiation:
    ```bash
    $ watch kubectl get pods --all-namespaces
    $ kubectl get nodes
    ```

 - Install bash-completion ([bash auto-completion on Linux](https://kubernetes.io/docs/tasks/tools/included/optional-kubectl-configs-bash-linux/)):
   ```bash
   $ sudo apt-get install bash-completion
   $ echo 'source /usr/share/bash-completion/bash_completion' >> ~/.bashrc
   ```

## Helm installation

 - From the article [Installing Helm](https://helm.sh/docs/intro/install/):
    ```bash
    $ curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    $ chmod 700 get_helm.sh
    $ ./get_helm.sh
    ```


## Rancher installation
 - From the article [Install Rancher on a Kubernetes Cluster](https://rancher.com/docs/rancher/v2.0-v2.4/en/installation/install-rancher-on-k8s/):
    ```bash
    # add Helm repo
    $ helm repo add rancher-latest https://releases.rancher.com/server-charts/latest

    # create Kubernetes namespace for Rancher
    $ kubectl create namespace cattle-system

    # install cert-manager
    $ kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.0.4/cert-manager.crds.yaml
    $ kubectl create namespace cert-manager
    $ helm repo add jetstack https://charts.jetstack.io
    $ helm repo update
    $ helm install \
         cert-manager jetstack/cert-manager \
         --namespace cert-manager \
         --version v1.1.0

    # install Rancher (only when the cert-manager pods are running)
    $ helm install rancher rancher-latest/rancher \
         --namespace cattle-system \
         --set hostname=controller

    # wait for Rancher to be rolled out
    $ kubectl -n cattle-system rollout status deploy/rancher
    ```


https://stackoverflow.com/questions/59484509/node-had-taints-that-the-pod-didnt-tolerate-error-when-deploying-to-kubernetes
