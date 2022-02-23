#!/usr/bin/env python3
import sys

from src.cmd import Command, Commands

sys.path.append("lib")

import logging
# Logger
logger = logging.getLogger(__name__)

from charms.osm.sshproxy import SSHProxyCharm
from ops.main import main

from ops.model import (
	ActiveStatus,
	MaintenanceStatus,
	BlockedStatus,
	WaitingStatus,
	ModelError,
)


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
		self.framework.observe(self.on.deploy_k8s_controller, self.on_deploy_k8s_controller)

	def on_config_changed(self, event):
		"""Handle changes in configuration"""
		super().on_config_changed(event)

	def on_install(self, event):
		"""Called when the charm is being installed"""
		super().on_install(event)

	def on_start(self, event):
		"""Called when the charm is being started"""
		super().on_start(event)

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
			
	##########################
	#     Custom Actions     #
	##########################
	def on_deploy_k8s_controller(self, event):
		self.__install_kubernetes(event)
		
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
		return commands.unit_run_command(logger=logger, proxy=proxy, unit_status=self.unit.status)

	def __disable_swap(self, event) -> bool:
		commands = Commands()

		# Add the Kubernetes repository
		commands.add_command(Command(
			cmd="""sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab""",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))
		commands.add_command(Command(
			cmd="sudo swapoff -a",
			initial_status="Installing curl and apt-transport-https packages...",
			ok_status="Installed curl and apt-transport-https",
			error_status="Couldn't install curl and apt-transport-https"
		))

		commands.add_command(Command(
			cmd="sudo modprobe overlay",
			initial_status="Adding GPG Google key...",
			ok_status="Added GPG Google key",
			error_status="Couldn't add GPG Google key"
		))
		commands.add_command(Command(
			cmd="sudo modprobe br_netfilter",
			initial_status="Adding Kubernetes repository...",
			ok_status="Kubernetes repository added",
			error_status="Couldn't add Kubernetes repository"
		))

		#
		commands.add_command(Command(
			cmd="""sudo tee /etc/sysctl.d/kubernetes.conf <<EOF
			net.bridge.bridge-nf-call-ip6tables = 1
			net.bridge.bridge-nf-call-iptables = 1
			net.ipv4.ip_forward = 1
			EOF""",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))


		commands.add_command(Command(
			cmd="sudo sysctl --system",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		proxy = self.get_ssh_proxy()
		return commands.unit_run_command(logger=logger, proxy=proxy, unit_status=self.unit.status)

	def __install_container_runtime(self):
		# Containerd
		commands = Commands()

		# Configure persistent loading of modules
		commands.add_command(Command(
			cmd="""sudo tee /etc/modules-load.d/containerd.conf <<EOF
			overlay
			br_netfilter
			EOF""",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))

		# Load at runtime
		commands.add_command(Command(
			cmd="sudo modprobe overlay",
			initial_status="Installing curl and apt-transport-https packages...",
			ok_status="Installed curl and apt-transport-https",
			error_status="Couldn't install curl and apt-transport-https"
		))
		commands.add_command(Command(
			cmd="sudo modprobe br_netfilter",
			initial_status="Adding GPG Google key...",
			ok_status="Added GPG Google key",
			error_status="Couldn't add GPG Google key"
		))

		# Ensure sysctl params are set
		commands.add_command(Command(
			cmd="""sudo tee /etc/sysctl.d/kubernetes.conf<<EOF
			net.bridge.bridge-nf-call-ip6tables = 1
			net.bridge.bridge-nf-call-iptables = 1
			net.ipv4.ip_forward = 1
			EOF""",
			initial_status="Adding Kubernetes repository...",
			ok_status="Kubernetes repository added",
			error_status="Couldn't add Kubernetes repository"
		))

		# Reload configs
		commands.add_command(Command(
			cmd="sudo sysctl --system",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))

		# Install required packages
		commands.add_command(Command(
			cmd="sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		# Add Docker repo
		commands.add_command(Command(
			cmd="curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))
		commands.add_command(Command(
			cmd="""sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) 
			stable""",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		# Install containerd
		commands.add_command(Command(
			cmd="sudo apt update",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))
		commands.add_command(Command(
			cmd="sudo apt install -y containerd.io",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		# Install containerd
		commands.add_command(Command(
			cmd="sudo mkdir -p /etc/containerd",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))
		commands.add_command(Command(
			cmd="sudo containerd config default>/etc/containerd/config.toml",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		# Restart containerd
		commands.add_command(Command(
			cmd="sudo systemctl restart containerd",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))
		commands.add_command(Command(
			cmd="sudo systemctl enable containerd",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))
		commands.add_command(Command(
			cmd="systemctl status  containerd",
			initial_status="Installing the kubelet, kubeadm and kubectl packages...",
			ok_status="Kubelet, kubeadm and kubectl packages installed",
			error_status="Couldn't install kubelet, kubeadm and kubectl packages"
		))

		proxy = self.get_ssh_proxy()
		return commands.unit_run_command(logger=logger, proxy=proxy, unit_status=self.unit.status)

	def __initialize_master_node(self):
		commands = Commands()

		# Enable kubelet service
		commands.add_command(Command(
			cmd="sudo systemctl enable kubelet",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))

		# Pull container images
		commands.add_command(Command(
			cmd="sudo kubeadm config images pull",
			initial_status="Updating system's package information...",
			ok_status="System packages' information updated",
			error_status="Couldn't update systems packages' information"
		))

		proxy = self.get_ssh_proxy()
		return commands.unit_run_command(logger=logger, proxy=proxy, unit_status=self.unit.status)


if __name__ == "__main__":
	main(SampleProxyCharm)
