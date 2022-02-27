#!/bin/sh


# Charm creation, adapted from the commands and files' contents examples given
# by the Day 1: VNF Services Initialization OSM Documentation
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
git submodule add https://github.com/canonical/operator mod/operator
git submodule add https://github.com/charmed-osm/charms.osm mod/charms.osm
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
	 install_dependencies(logger=logger)
    main(SampleProxyCharm)

EOF

cat <<EOF > src/command.py
import sys
from logging import Logger
from typing import List

sys.path.append("lib")

from charms.osm.sshproxy import SSHProxy

from ops.model import (
   StatusBase,
   MaintenanceStatus,
    BlockedStatus,
     ActiveStatus
)


class Command:
   def __init__(self, cmd: str, initial_status: str, ok_status: str, error_status: str) -> None:
      self.cmd = cmd
      self.initial_status = initial_status
      self.ok_status = ok_status
      self.error_status = error_status


class Commands:
   def __init__(self, commands: List[Command] = None) -> None:
      self.commands = []

      if commands:
         self.commands = commands.copy()
  
   def __iter__(self) -> None:
      self.n = 0
      return self

   def __next__(self) -> None:
      if self.n < len(self.commands):
         result = self.commands[self.n]
         self.n += 1
         return result
      else:
         raise StopIteration

   def add_command(self, new_command: Command) -> None:
      self.commands.append(new_command)

   def unit_run_command(self, component: str, logger: Logger, proxy: SSHProxy, unit_status: StatusBase) -> bool:
      for i in range(len(self.commands)):
         result, error = None, None
         unit_status = MaintenanceStatus(self.commands[i].initial_status)
         try:
            result, error = proxy.run(self.commands[i].cmd)
            logger.info(f"Status: {self.commands[i].ok_status}; Output: {result}; Errors: {error}")
            unit_status = MaintenanceStatus(self.commands[i].ok_status)
         except Exception as e:
            logger.error(f"[{self.commands[i].error_status}] failed {e}. Stderr: {error}")
            unit_status = BlockedStatus(self.commands[i].error_status)
            raise Exception(f"[Unable to <{component}>]; Status: {self.commands[i].error_status}; Action failed {e}; Stderr: {error}")

      unit_status = ActiveStatus(f"<{component}> completed with success")
      return True

EOF

cat <<EOF > src/dependencies.py
import os
import subprocess
from logging import Logger

def install_dependencies(logger: Logger):
   python_requirements = ["packaging==21.3"]

   # Update the apt cache
   logger.info("Updating packages...")
   subprocess.check_call(["sudo", "apt-get", "update"])

   # Make sure Python3 + PIP are available
   if not os.path.exists("/usr/bin/python3") or not os.path.exists("/usr/bin/pip3"):
      # This is needed when running as a k8s charm, as the ubuntu:latest
      # image doesn't include either package.
      # Install the Python3 package
      subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3", "python3-pip"])

   # Install the build dependencies for our requirements (paramiko)
   logger.info("Installing libffi-dev and libssl-dev ...")
   subprocess.check_call(["sudo", "apt-get", "install", "-y", "libffi-dev", "libssl-dev"])

   if len(python_requirements) > 0:
      logger.info("Installing python3 modules")
      subprocess.check_call(["sudo", "python3", "-m", "pip", "install"] + python_requirements)

EOF
