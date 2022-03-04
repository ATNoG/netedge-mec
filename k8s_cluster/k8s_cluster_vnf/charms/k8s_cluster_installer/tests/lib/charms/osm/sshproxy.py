import io
import ipaddress
from packaging import version
import subprocess
import os
import socket
import shlex
import traceback
import sys
import yaml
from shutil import which
from subprocess import (
   check_call,
   Popen,
   CalledProcessError,
   PIPE,
)
import os
import subprocess
import logging

from lib.charms.osm.on import OnMock
from ops.model import Model, Unit

logger = logging.getLogger(__name__)

class FrameworkMock:
   def observe(self, a, b):
      pass

class SSHProxyCharm():
   def __init__(self, *args):
      self.framework = FrameworkMock()
      self.on = OnMock()
      self.unit = Unit()
      self.model = Model(self.unit)

   def get_ssh_proxy(self):
      """Get the SSHProxy instance"""
      proxy = SSHProxy(
         hostname=self.model.config["ssh-hostname"],
         username=self.model.config["ssh-username"],
         password=self.model.config["ssh-password"],
      )
      return proxy

   def on_proxypeer_relation_changed(self, event):
      if self.peers.is_cluster_initialized and not SSHProxy.has_ssh_key():
         pubkey = self.peers.ssh_public_key
         privkey = self.peers.ssh_private_key
         SSHProxy.write_ssh_keys(public=pubkey, private=privkey)
         self.verify_credentials()
      else:
         event.defer()

   def on_config_changed(self, event):
      """Handle changes in configuration"""
      self.verify_credentials()

   def on_install(self, event):
      SSHProxy.install()

   def on_start(self, event):
      """Called when the charm is being installed"""
      if not self.peers.is_joined:
         event.defer()
         return

      if not SSHProxy.has_ssh_key():
         pubkey = None
         privkey = None
         if self.unit.is_leader():
            if self.peers.is_cluster_initialized:
               SSHProxy.write_ssh_keys(
                  public=self.peers.ssh_public_key,
                  private=self.peers.ssh_private_key,
               )
            else:
               SSHProxy.generate_ssh_key()
               self.on.ssh_keys_initialized.emit(
                  SSHProxy.get_ssh_public_key(), SSHProxy.get_ssh_private_key()
               )
      self.verify_credentials()

   def verify_credentials(self):
      proxy = self.get_ssh_proxy()
      verified, _ = proxy.verify_credentials()
      return True

   #####################
   # SSH Proxy methods #
   #####################
   def on_generate_ssh_key_action(self, event):
      """Generate a new SSH keypair for this unit."""
      if self.model.unit.is_leader():
         if not SSHProxy.generate_ssh_key():
            event.fail("Unable to generate ssh key")
      else:
         event.fail("Unit is not leader")
         return

   def on_get_ssh_public_key_action(self, event):
      """Get the SSH public key for this unit."""
      if self.model.unit.is_leader():
         pubkey = SSHProxy.get_ssh_public_key()
         event.set_results({"pubkey": SSHProxy.get_ssh_public_key()})
      else:
         event.fail("Unit is not leader")
         return

   def on_run_action(self, event):
      """Run an arbitrary command on the remote host."""
      if self.model.unit.is_leader():
         cmd = event.params["command"]
         proxy = self.get_ssh_proxy()
         stdout, stderr = proxy.run(cmd)
         event.set_results({"output": stdout})
         if len(stderr):
            event.fail(stderr)
      else:
         event.fail("Unit is not leader")
         return

   def on_verify_ssh_credentials_action(self, event):
      """Verify the SSH credentials for this unit."""
      unit = self.model.unit
      if unit.is_leader():
         proxy = self.get_ssh_proxy()
         verified, stderr = proxy.verify_credentials()
         if verified:
            event.set_results({"verified": True})
         else:
            event.set_results({"verified": False, "stderr": stderr})
            event.fail("Not verified")
      else:
         event.fail("Unit is not leader")
         return

class SSHProxy:
   def __init__(self, hostname: str, username: str, password: str = ""):
      self.hostname = hostname
      self.username = username
      self.password = password

   def run(self, cmd):
      """Run a command remotely via SSH.
      Note: The previous behavior was to run the command locally if SSH wasn't
      configured, but that can lead to cases where execution succeeds when you'd
      expect it not to.
      """
      if isinstance(cmd, str):
         cmd = shlex.split(cmd)

      host = self.hostname
      user = self.username
      passwd = self.password

      # Make sure we have everything we need to connect
      if host and user:
         return self.ssh(cmd)

      raise Exception("Invalid SSH credentials.")

   def scp(self, source_file, destination_file):
      """Execute an scp command. Requires a fully qualified source and
      destination.
      :param str source_file: Path to the source file
      :param str destination_file: Path to the destination file
      :raises: :class:`CalledProcessError` if the command fails
      """
      if which("sshpass") is None:
         SSHProxy.install()
      cmd = [
         "sshpass",
         "-p",
         self.password,
         "scp",
      ]
      destination = "{}@{}:{}".format(self.username, self.hostname, destination_file)
      cmd.extend([source_file, destination])
      subprocess.run(cmd, check=True)

   def ssh(self, command):
      """Run a command remotely via SSH.
      :param list(str) command: The command to execute
      :return: tuple: The stdout and stderr of the command execution
      :raises: :class:`CalledProcessError` if the command fails
      """

      destination = "{}@{}".format(self.username, self.hostname)
      cmd = [
         "sshpass",
         "-p",
         self.password,
         "ssh",
         destination,
      ]
      cmd.extend(command)
      print(cmd)
      
      # output = subprocess.run(
      #    cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
      # )
      # return (
      #    output.stdout.decode("utf-8").strip(),
      #    output.stderr.decode("utf-8").strip(),
      # )
      
      return (None, None)
