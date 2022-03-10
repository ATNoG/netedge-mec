#!/usr/bin/env python3
import shlex
import sys
import logging
import re
# Logger
logger = logging.getLogger(__name__)

from dependencies import install_dependencies

install_dependencies(logger=logger)

from versions import PackageVersions
from command import Command, Commands
from utils import generate_random_k8s_compliant_hostname

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

        # Automatic custom actions
        self.framework.observe(self.on.deploy_k8s_controller_action, self.on_deploy_k8s_controller)
        self.framework.observe(self.on.deploy_k8s_workers_action, self.on_deploy_k8s_workers)
        
        # Manual custom actions
        self.framework.observe(self.on.get_k8s_controller_info_action, self.on_get_k8s_controller_info)
        self.framework.observe(self.on.join_k8s_workers_action, self.on_join_k8s_workers)
        self.framework.observe(self.on.remove_k8s_worker_action,self.on_remove_k8s_worker_action)
        
        # OSM actions (primitives)
        self.framework.observe(self.on.start_action, self.on_start_action)
        self.framework.observe(self.on.stop_action, self.on_stop_action)
        self.framework.observe(self.on.restart_action, self.on_restart_action)
        self.framework.observe(self.on.reboot_action, self.on_reboot_action)
        self.framework.observe(self.on.upgrade_action, self.on_upgrade_action)

    def on_config_changed(self, event):
        """Handle changes in configuration"""
        super().on_config_changed(event)

    def on_install(self, event):
        """Called when the charm is being installed"""
        super().on_install(event)

    def on_start(self, event):
        """Called when the charm is being started"""
        super().on_start(event)

        entity_deployment = self.model.config['entity']

        if entity_deployment == 'controller':
            self.on_deploy_k8s_controller(event)
        elif entity_deployment == 'worker':
            self.on_deploy_k8s_workers(event)

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
    #         Controller     #
    ##########################
    def on_deploy_k8s_controller(self, event) -> None:
        self.__install_kubernetes(event)
        self.__disable_swap(event)
        self.__install_container_runtime(event)
        self.__initialize_master_node(event)
        self.__define_dns_name(event, name='controller')
        self.__create_cluster(event)
        self.__configure_kubectl(event)
        self.__install_network_plugin(event)

    ##########################
    #     Custom Actions     #
    #             Worker     #
    ##########################
    def on_deploy_k8s_workers(self, event) -> None:
        self.__install_kubernetes(event)
        self.__disable_swap(event)
        self.__install_container_runtime(event)

        current_hostname = self.__obtain_current_hostname(event)
        hostname = generate_random_k8s_compliant_hostname(current_hostname=current_hostname)
        self.__define_dns_name(event, name=hostname)

    def on_get_k8s_controller_info(self, event):
        controller_hostname, controller_port = self.__get_cluster_info(event)
        controller_ip = self.__get_certain_node_ip(event)
        join_token = self.__generate__join__token(event)
        ca_cert_hash = self.__get_ca_cert_hash(event)
        
        event.set_results({
            'controller-hostname': controller_hostname,
            'controller-port': controller_port,
            'controller-ip': controller_ip,
            'join-token': join_token,
            'ca-cert-hash': ca_cert_hash
        })

    def on_join_k8s_workers(self, event) -> None:
        self.__join_node_to_cluster(event)

    def on_remove_k8s_worker_action(self, event) -> None:
        self.__remove_worker_from_cluster(event)
        
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
            cmd=f"sudo apt -y install curl={PackageVersions.curl} apt-transport-https={PackageVersions.apt_transport_https}",
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
            cmd=f"sudo apt -y install git={PackageVersions.git} wget={PackageVersions.wget} "
                f"kubelet={PackageVersions.kubelet} kubeadm={PackageVersions.kubeadm} kubectl={PackageVersions.kubectl}",
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
        commands.unit_run_command(component="Install Kubernetes", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

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
        commands.unit_run_command(component="Disable swap", logger=logger, proxy=proxy, unit_status=self.unit.status)
        logger.info(f"status: {self.unit.status}")

    def __install_container_runtime(self, event) -> None:
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
            cmd=""" "echo -e '"'net.bridge.bridge-nf-call-ip6tables = 1\nnet.bridge.bridge-nf-call-iptables = 1\nnet.ipv4.ip_forward = 1'"'" 
         | sudo tee /etc/sysctl.d/kubernetes.conf > /dev/null""",
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
            cmd=f"sudo apt install -y gnupg2={PackageVersions.gnupg2} "
                f"software-properties-common={PackageVersions.software_properties_common} "
                f"ca-certificates={PackageVersions.ca_certificates}",
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
            cmd=f"sudo apt install -y containerd.io={PackageVersions.containerd_io}",
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

        # Wait for Containerd service to start
        number_trials = 10
        commands.add_command(Command(
            cmd=f"for i in {{1..{number_trials}}}; do echo 1; sleep 60; if systemctl is-active --quiet containerd; "
                f"then break; fi; done",
            initial_status="Waiting for the Containerd service to be active...",
            ok_status="Containerd service is active",
            error_status="Couldn't wait for the Containerd service to be active"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Install Containerd", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

    def __initialize_master_node(self, event) -> None:
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
        commands.unit_run_command(component="Initialize master node", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

    def __define_dns_name(self, event, name) -> None:
        commands = Commands()

        commands.add_command(Command(
            cmd=f"echo 127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4 {name} | sudo tee "
                f"/etc/hosts;"
                f"echo ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 {name} | sudo "
                f"tee -a /etc/hosts",
            initial_status="Updating the host's DNS name on the hosts file...",
            ok_status="Host's DNS name updated on the hosts file",
            error_status="Couldn't update the host's DNS name on the hosts file"
        ))
        commands.add_command(Command(
            cmd=f"sudo hostnamectl set-hostname {name}",
            initial_status="Updating the host's DNS name with hostnamectl...",
            ok_status="Host's DNS name updated with hostnamectl",
            error_status="Couldn't update the host's DNS name with hostnamectl"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Define DNS name", logger=logger, proxy=proxy, unit_status=self.unit.status)
        
    def __obtain_current_hostname(self, event) -> str:
        commands = Commands()

        commands.add_command(Command(
            cmd="hostname",
            initial_status="Obtaining node's current hostname...",
            ok_status="Obtained node's current hostname",
            error_status="Couldn't obtain node's current hostname"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Obtain current hostname", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)
        
        return commands.commands[0].result.strip()

    def __create_cluster(self, event) -> None:
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
        commands.unit_run_command(component="Create the cluster", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

    def __configure_kubectl(self, event) -> None:
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
        commands.unit_run_command(component="Configure kubectl", logger=logger, proxy=proxy, unit_status=self.unit.status)

    def __install_network_plugin(self, event) -> None:
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
        commands.unit_run_command(component="Install Calico's network plugin", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

    ##########################
    #     Custom Actions     #
    #     For Cluster Join   #
    ##########################
    def __get_cluster_info(self, event) -> str:
        """
        Obtains information about the cluster information such as HOSTNAME and PORT
        Used by new worker nodes to connect to the cluster
        """
        commands = Commands()
        # If possible add sed command replacing // with nothing
        # python shlex wasn't really "colaborating" with this replace 
        commands.add_command(Command(
            cmd=f""" kubectl cluster-info | head -n 1 | cut -d '"':'"' -f2,3""",
            initial_status="Obtaining cluster information...",
            ok_status="Obtained cluster information",
            error_status="Couldn't obtain information about the cluster"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Obtaining cluster information", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)
        
        # We are getting the output from a kubectl command which uses ANSI colors, that
        # unfortunatelly alters the expected result so we have to remove the ANSI colors from
        # the output
        ansi_result = commands.commands[0].result
        # Regex to escape ANSI color
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        # The output at this moment will look like //hostname:port
        # to obtain only the hostname and port do a simple string conversion
        result = ansi_escape.replace("//","").split(":")
        return result

    def __get_certain_node_ip(self, event, node_name="controller") -> str:
        """
        Obtains IP information about several nodes
        The IP from nodes isn't restrained to worker nodes, by specifying the name we can obtain ip from any node of the cluster
        This is useful if the VDU has more than one interface (i.e is using one interface for the cluster and another
        to communicate with the OSM). The actual IP required for new nodes to connect is the IP from the cluster and not the one the OSM knows.
        """
        commands = Commands()

        commands.add_command(Command(
            cmd=f"""kubectl get nodes -o jsonpath='"'{{.items[?(@.metadata.name=="'"{node_name}"'")].status.addresses[?(@.type=="'"InternalIP"'")].address}}'"' """,
            initial_status="Obtaining node ip address...",
            ok_status=f"Node {node_name} ip address retrieved successfully.",
            error_status="Couldn't obtain node ip address"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Obtain node ip address", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

        return commands.commands[0].result

    def __generate__join__token(self, event) -> str:
        """Generates a new token for every node attempting to join"""
        commands = Commands()

        commands.add_command(Command(
            cmd=f"kubeadm token create",
            initial_status="Creating a new token to be used for joining the cluster",
            ok_status="Token successfully created",
            error_status="Couldn't not create a new join token"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Cluster join token generator", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

        return commands.commands[0].result

    def __get_ca_cert_hash(self, event) -> str:
        """Obtains the ca certificate hash of the master node"""
        commands = Commands()

        # When using commands that require a lot of " characters beware of their usage
        # In this case we enclose " and the space character with '' , this allows for the literal value to be used
        # e.g sed "s/^.* //" would end up as ["sed", "'s/^.*'", "'//'"] which is not the command we want
        # the command we actually want is ["sed", "s/^.* //"] which is achievable by using the enclosing in the " and space
        # character ending up with the following result sed '"'s/^.*' '//'"'
        commands.add_command(Command(
            cmd=f"""openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed '"'s/^.*' '//'"' """,
            initial_status="Obtaining hash of the ca cert",
            ok_status="Ca cert hash was obtained",
            error_status="Couldn't obtain ca cert hash"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Obtain master ca cert hash", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

        return commands.commands[0].result

    def __join_node_to_cluster(self, event) -> None:
        """ Joins a node to a cluster """
        commands = Commands()

        # Obtain the information about the master node
        master_ip = event.params['ip']
        master_host = event.params['host']
        master_port = event.params['port']
        master_token = event.params['token']
        master_cert = event.params['cert']

        # Add master info to worker node
        commands.add_command(Command(
            cmd=f"echo {master_ip} {master_host} | sudo tee -a /etc/hosts;",
            initial_status="Adding the master IP to worker node host file...",
            ok_status="Master IP was successfully added to worker node known hosts",
            error_status="Couldn't update the known hosts file"
        ))

        # Join the master
        commands.add_command(Command(
            cmd=f"sudo kubeadm join {master_ip}:{master_port} "
                f"--token {master_token} "
                f"--discovery-token-ca-cert-hash sha256:{master_cert}",
            initial_status="Joining a new worker node to cluster",
            ok_status="Node was successfully joined the cluster",
            error_status="Node couldn't join"
        ))

        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Join a node to the cluster", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)

    def __remove_worker_from_cluster(self, event) -> None:
        """
        Given a Node's Hostname, remove it from a given Cluster
        The VDU will still exist, but it is not part of the cluster anymore
        """
        commands = Commands()
        
        # Obtain the name of the node
        node_hostname = event.params['node']
        
        # Drain the node (i.e remove all the pods from the worker node)
        # Ignores daemonsets (feature that ensures all nodes run a copy of a certain pod)
        # Since we want to remove the node this has no impact
        commands.add_command(Command(
            cmd=f"kubectl drain {node_hostname} --ignore-daemonsets",
            initial_status=f"Draining node {node_hostname} from the cluster...",
            ok_status="Node successfully drain from the cluster",
            error_status="Failed to drain node from cluster"
        ))
        
        # Remove the node from the worker node 
        # After removing the node the daemonset pods may still hang for a while
        commands.add_command(Command(
            cmd=f"kubectl delete node {node_hostname}",
            initial_status=f"Deleting node {node_hostname} from the cluster...",
            ok_status="Node successfully removed from the cluster",
            error_status="Failed to remove node from cluster"
        ))
    
        proxy = self.get_ssh_proxy()
        commands.unit_run_command(component="Remove worker from cluster", logger=logger, proxy=proxy,
                                  unit_status=self.unit.status)
if __name__ == "__main__":
    main(SampleProxyCharm)
