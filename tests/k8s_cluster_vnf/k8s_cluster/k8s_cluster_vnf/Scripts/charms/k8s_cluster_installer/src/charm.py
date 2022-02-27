#!/usr/bin/env python3
import shlex
import sys
import logging

from command import Command, Commands
from dependencies import install_dependencies

sys.path.append("lib")

from charms.osm.sshproxy import SSHProxyCharm
from ops.main import main
from ops.model import (
   ActiveStatus,
   MaintenanceStatus,
   BlockedStatus,
   WaitingStatus,
   ModelError,
)

# Logger
logger = logging.getLogger(__name__)

class SampleProxyCharm(SSHProxyCharm):
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)
      # self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)

      # Listen to the touch action event
      self.framework.observe(self.on.configure_remote_action, self.configure_remote)
      self.framework.observe(self.on.start_service_action, self.start_service)
      
      # Custom actions
      self.framework.observe(self.on.deploy_k8s_controller_action, self.on_deploy_k8s_controller)
      self.framework.observe(self.on.deploy_k8s_workers_action, self.on_deploy_k8s_workers)
      
      # OSM actions (primitives)
      # self.framework.observe(self.on.start_action, self.on_start_action)
      # self.framework.observe(self.on.stop_action, self.on_stop_action)
      # self.framework.observe(self.on.restart_action, self.on_restart_action)
      # self.framework.observe(self.on.reboot_action, self.on_reboot_action)
      # self.framework.observe(self.on.upgrade_action, self.on_upgrade_action)

   def on_config_changed(self, event):
      """Handle changes in configuration"""
      super().on_config_changed(event)

   def on_install(self, event):
      """Called when the charm is being installed"""
      super().on_install(event)

   def on_start(self, event):
      """Called when the charm is being started"""
      super().on_start(event)
      self.on_deploy_k8s_controller(event)

   def configure_remote(self, event):
      """Configure remote action."""

      if self.model.unit.is_leader():
         stderr = None
         try:
            mgmt_ip = self.model.config["ssh-hostname"]
            destination_ip = event.params["destination_ip"]
            cmd = "vnfcli set license {} server {}".format(
               mgmt_ip,
               destination_ip
            )
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run(cmd)
            event.set_results({"output": stdout})
         except Exception as e:
            event.fail("Action failed {}. Stderr: {}".format(e, stderr))
      else:
         event.fail("Unit is not leader")

   def start_service(self, event):
      """Start service action."""

      if self.model.unit.is_leader():
         stderr = None
         try:
            cmd = "sudo service vnfoper start"
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run(cmd)
            event.set_results({"output": stdout})
         except Exception as e:
            event.fail("Action failed {}. Stderr: {}".format(e, stderr))
      else:
         event.fail("Unit is not leader")
         
   ###############
   # OSM methods #
   ###############
   def on_start_action(self, event):
      """Start the VNF service on the VM."""
      pass

   def on_stop_action(self, event):
      """Stop the VNF service on the VM."""
      pass

   def on_restart_action(self, event):
      """Restart the VNF service on the VM."""
      pass

   def on_reboot_action(self, event):
      """Reboot the VM."""
      if self.unit.is_leader():
         pass

   def on_upgrade_action(self, event):
      """Upgrade the VNF service on the VM."""
      pass
       
   ##########################
   #     Custom Actions     #
   ##########################
   def on_deploy_k8s_controller(self, event):
      self.__install_kubernetes(event)
      self.__disable_swap(event)
      self.__install_container_runtime(event)
      self.__initialize_master_node(event)
      self.__define_dns_name(event, name='controller')
      self.__create_cluster(event)
      self.__configure_kubectl(event)
      self.__install_network_plugin(event)
      
   def on_deploy_k8s_workers(self, event):
      self.__install_kubernetes(event)
      self.__disable_swap(event)
      self.__install_container_runtime(event)
      
      # TODO -> ver como meter vários depois
      self.__define_dns_name(event, name='worker1')
      
      # TODO -> kubeadm join

   ##########################
   #        Functions       #
   ##########################
   def __install_kubernetes(self, event) -> bool:
      commands = Commands()

      # Add the Kubernetes repository
      commands.add_command(Command(
         cmd="sudo apt update",
         initial_status="Updating system's package information...",
         ok_status="System packages' information updated",
         error_status="Couldn't update systems packages' information"
      ))
      commands.add_command(Command(
         cmd="sudo apt -y install curl apt-transport-https",
         initial_status="Installing curl and apt-transport-https packages...",
         ok_status="Installed curl and apt-transport-https",
         error_status="Couldn't install curl and apt-transport-https"
      ))
      commands.add_command(Command(
         cmd="curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -",
         initial_status="Adding GPG Google key...",
         ok_status="Added GPG Google key",
         error_status="Couldn't add GPG Google key"
      ))
      commands.add_command(Command(
         cmd="""echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee 
         /etc/apt/sources.list.d/kubernetes.list""",
         initial_status="Adding Kubernetes repository...",
         ok_status="Kubernetes repository added",
         error_status="Couldn't add Kubernetes repository"
      ))

      # Install kubelet, kubeadm and kubectl
      commands.add_command(Command(
         cmd="sudo apt update",
         initial_status="Updating system's package information...",
         ok_status="System packages' information updated",
         error_status="Couldn't update systems packages' information"
      ))
      commands.add_command(Command(
         cmd="sudo apt -y install vim git curl wget kubelet=1.22.7-00 kubeadm=1.22.7-00 kubectl=1.22.7-00",
         initial_status="Installing the kubelet, kubeadm and kubectl packages...",
         ok_status="Kubelet, kubeadm and kubectl packages installed",
         error_status="Couldn't install kubelet, kubeadm and kubectl packages"
      ))
      commands.add_command(Command(
         cmd="sudo apt-mark hold kubelet kubeadm kubectl",
         initial_status="Holding the kubelet, kubeadm and kubectl packages...",
         ok_status="Kubelet, kubeadm and kubectl packages held",
         error_status="Couldn't held kubelet, kubeadm and kubectl packages"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Install Kubernetes", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __disable_swap(self, event) -> bool:
      commands = Commands()

      # Add the Kubernetes repository
      commands.add_command(Command(
         cmd="""sudo sed -i "'/ swap / s/^/#/'" /etc/fstab""",
         initial_status="Saving swap off persistent configuration ...",
         ok_status="Swap off persistent configuration saved",
         error_status="Couldn't update swap off persistent configuration"
      ))
      commands.add_command(Command(
         cmd="sudo swapoff -a",
         initial_status="Disabling swap...",
         ok_status="Swap disabled",
         error_status="Couldn't disable swap"
      ))

      proxy = self.get_ssh_proxy()
      result = commands.unit_run_command(component="Disable swap", logger=logger, proxy=proxy, unit_status=self.unit.status)
      logger.info(f"status: {self.unit.status}")
      return result

   def __install_container_runtime(self, event):
      # Containerd
      commands = Commands()

      # Configure persistent loading of modules
      commands.add_command(Command(
         cmd=""" "echo -e '"'overlay\nbr_netfilter'"'" | sudo tee /etc/modules-load.d/containerd.conf > /dev/null""",
         initial_status="Configuring persistent loading of modules...",
         ok_status="Persistent loading of modules configured",
         error_status="Couldn't configure persistent loading of modules"
      ))

      # Load at runtime
      commands.add_command(Command(
         cmd="sudo modprobe overlay",
         initial_status="Adding <overlay> kernel module...",
         ok_status="<overlay> kernel module added",
         error_status="Couldn't add <overlay> module"
      ))
      commands.add_command(Command(
         cmd="sudo modprobe br_netfilter",
         initial_status="Adding <br_netfilter> kernel module...",
         ok_status="<br_netfilter> kernel module added",
         error_status="Couldn't add <br_netfilter> module"
      ))

      # Ensure sysctl params are set
      commands.add_command(Command(
         cmd=""" "echo -e '"'net.bridge.bridge-nf-call-ip6tables = 1\nnet.bridge.bridge-nf-call-iptables = 1\nnet.ipv4.ip_forward = 1'"'" | sudo tee /etc/sysctl.d/kubernetes.conf > /dev/null""",
         initial_status="Updating sysctl settings...",
         ok_status="Sysctl settings updated",
         error_status="Couldn't update sysctl settings"
      ))

      # Reload configs
      commands.add_command(Command(
         cmd="sudo sysctl --system",
         initial_status="Reloading sysctl...",
         ok_status="Sysctl reloaded",
         error_status="Couldn't reload sysctl"
      ))

      # Install required packages
      commands.add_command(Command(
         cmd="sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates",
         initial_status="Installing required packages for Containerd...",
         ok_status="Required packages for Containerd packages installed",
         error_status="Couldn't install required packages for Containerd"
      ))

      # Add Docker repo
      commands.add_command(Command(
         cmd="curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -",
         initial_status="Adding GPG Docker key...",
         ok_status="Added GPG Docker key",
         error_status="Couldn't add GPG Docker key"
      ))
      commands.add_command(Command(
         cmd="""sudo add-apt-repository '"'deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable'"'""",
         initial_status="Adding Docker repository...",
         ok_status="Docker repository added",
         error_status="Couldn't add Docker repository"
      ))

      # Install Containerd
      commands.add_command(Command(
         cmd="sudo apt update",
         initial_status="Updating system's package information...",
         ok_status="System packages' information updated",
         error_status="Couldn't update systems packages' information"
      ))
      commands.add_command(Command(
         cmd="sudo apt install -y containerd.io",
         initial_status="Installing Containerd...",
         ok_status="Containerd installed",
         error_status="Couldn't install Containerd"
      ))

      # Configure Containerd
      commands.add_command(Command(
         cmd="sudo mkdir -p /etc/containerd && containerd config default | sudo tee /etc/containerd/config.toml > /dev/null",
         initial_status="Configuring Containerd...",
         ok_status="Containerd configured",
         error_status="Couldn't configure Containerd"
      ))

      # Restart Containerd
      commands.add_command(Command(
         cmd="sudo systemctl restart containerd",
         initial_status="Restarting Containerd service...",
         ok_status="Containerd service restarted",
         error_status="Couldn't restart Containerd service"
      ))
      commands.add_command(Command(
         cmd="sudo systemctl enable containerd",
         initial_status="Enabling Containerd service...",
         ok_status="Containerd service enabled",
         error_status="Couldn't enable Containerd service"
      ))

      # TODO -> VER DISTO
      commands.add_command(Command(
         cmd="while ! systemctl is-active --quiet containerd; do sleep 10; done",
         initial_status="Waiting for the Containerd service to be active...",
         ok_status="Containerd service is active",
         error_status="Couldn't wait for the Containerd service to be active"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Install Containerd", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __initialize_master_node(self, event):
      commands = Commands()

      # Enable kubelet service
      commands.add_command(Command(
         cmd="sudo systemctl enable kubelet",
         initial_status="Enabling kubelet service...",
         ok_status="Kubelet service enabled",
         error_status="Couldn't enable Kubelet service"
      ))

      # Pull container images
      commands.add_command(Command(
         cmd="sudo kubeadm config images pull",
         initial_status="Pulling Kubeadm container images...",
         ok_status="Kubeadm container imaged pulled",
         error_status="Couldn't pull Kubeadm container images"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Initialize master node", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __define_dns_name(self, event, name):
      commands = Commands()

      commands.add_command(Command(
         cmd=f"echo 127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4 {name} | sudo tee "
             f"/etc/hosts;"
             f"echo ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 {name} | sudo "
             f"tee /etc/hosts",
         initial_status="Updating the host's DNS name on the hosts file...",
         ok_status="Host's DNS name updated on the hosts file",
         error_status="Couldn't update the host's DNS name on the hosts file"
      ))
      commands.add_command(Command(
         cmd="sudo hostnamectl set-hostname {name}",
         initial_status="Updating the host's DNS name with hostnamectl...",
         ok_status="Host's DNS name updated with hostnamectl",
         error_status="Couldn't update the host's DNS name with hostnamectl"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Define DNS name", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __create_cluster(self, event):
      commands = Commands()

      commands.add_command(Command(
         cmd="""sudo kubeadm init \
         --pod-network-cidr=192.168.0.0/16 \
         --upload-certs \
         --control-plane-endpoint=controller""",
         initial_status="Creating the cluster...",
         ok_status="Cluster created with success",
         error_status="Couldn't create the cluster"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Create the cluster", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __configure_kubectl(self, event):
      commands = Commands()

      commands.add_command(Command(
         cmd="mkdir -p $HOME/.kube && "
             "sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config && "
             "sudo chown $(id -u):$(id -g) $HOME/.kube/config",
         initial_status="Configuring kubectl...",
         ok_status="Kubectl configured",
         error_status="Couldn't configure kubectl"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Configure kubectl", logger=logger, proxy=proxy, unit_status=self.unit.status)

   def __install_network_plugin(self, event):
      commands = Commands()

      # Install Calico
      commands.add_command(Command(
         cmd="kubectl create -f https://docs.projectcalico.org/manifests/tigera-operator.yaml && "
             "kubectl create -f https://docs.projectcalico.org/manifests/custom-resources.yaml",
         initial_status="Installing Calico network plugin...",
         ok_status="Calico network plugin installed",
         error_status="Couldn't install Calico network plugin"
      ))

      proxy = self.get_ssh_proxy()
      return commands.unit_run_command(component="Install Calico's network plugin", logger=logger, proxy=proxy, unit_status=self.unit.status)


if __name__ == "__main__":
   install_dependencies(logger=logger)
   main(SampleProxyCharm)
