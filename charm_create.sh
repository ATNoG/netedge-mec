#!/bin/sh


# Charm creation, with the commands and files' contents examples given by the Day
# 1: VNF Services Initialization OSM Documentation
# (https://osm.etsi.org/docs/vnf-onboarding-guidelines/03-day1.html)


if [ $# -eq 0 ]; then
   echo "You must give a name for the charm you want to create."
   exit 1
fi

charm_name=$1

if [[ -d $charm_name ]]; then
   echo "$charm_name already exists."
   exit 1
fi

mkdir -p $charm_name/
cd $charm_name/
mkdir hooks lib mod src
touch src/charm.py
touch actions.yaml metadata.yaml config.yaml
chmod +x src/charm.py
ln -s ../src/charm.py hooks/upgrade-charm
ln -s ../src/charm.py hooks/install
ln -s ../src/charm.py hooks/start
git clone https://github.com/canonical/operator mod/operator
git clone https://github.com/charmed-osm/charms.osm mod/charms.osm
ln -s ../mod/operator/ops lib/ops
ln -s ../mod/charms.osm/charms lib/charms

cat <<EOF > metadata.yaml
name: samplecharm
summary: this is an example
maintainer: David Garcia <david.garcia@canonical.com>
description: |
  This is an example of a proxy charm deployed by Open Source Mano.
tags:
  - nfv
subordinate: false
series:
  - bionic
  - xenial
peers: # This will give HA capabilities to your Proxy Charm
  proxypeer:
    interface: proxypeer
EOF

cat <<EOF > config.yaml
options:
  ssh-hostname:
    type: string
    default: ""
    description: "The hostname or IP address of the machine to"
  ssh-username:
    type: string
    default: ""
    description: "The username to login as."
  ssh-password:
    type: string
    default: ""
    description: "The password used to authenticate."
  ssh-public-key:
    type: string
    default: ""
    description: "The public key of this unit."
  ssh-key-type:
    type: string
    default: "rsa"
    description: "The type of encryption to use for the SSH key."
  ssh-key-bits:
    type: int
    default: 4096
    description: "The number of bits to use for the SSH key."
EOF

cat <<EOF > actions.yaml
# Actions to be implemented in src/charm.py
configure-remote:
  description: "Configures the remote server"
  params:
    destination_ip:
      description: "IP of the remote server"
      type: string
      default: ""
  required:
    - destination_ip
start-service:
  description: "Starts the service of the VNF"

# Required by charms.osm.sshproxy
run:
  description: "Run an arbitrary command"
  params:
    command:
      description: "The command to execute."
      type: string
      default: ""
  required:
    - command
generate-ssh-key:
  description: "Generate a new SSH keypair for this unit. This will replace any existing previously generated keypair."
verify-ssh-credentials:
  description: "Verify that this unit can authenticate with server specified by ssh-hostname and ssh-username."
get-ssh-public-key:
  description: "Get the public SSH key for this unit."
EOF

cat <<EOF > src/charm.py
#!/usr/bin/env python3
import sys

sys.path.append("lib")

from charms.osm.sshproxy import SSHProxyCharm
from ops.main import main


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


if __name__ == "__main__":
    main(SampleProxyCharm)
EOF
