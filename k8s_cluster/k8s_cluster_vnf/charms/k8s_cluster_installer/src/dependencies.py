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
