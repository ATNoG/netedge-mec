#!/usr/bin/env python3
import shlex
import sys
import logging

# Logger
logger = logging.getLogger(__name__)

from dependencies import install_dependencies
install_dependencies(logger=logger)

from command import Command, Commands

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
        
        # Custom actions
        self.framework.observe(self.on.install_requirements_action, self.on_install_requirements)
        
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
        
        self.on_install_requirements(event)

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
    def on_install_requirements(self, event) -> None:
        pass


if __name__ == "__main__":
    main(SampleProxyCharm)
