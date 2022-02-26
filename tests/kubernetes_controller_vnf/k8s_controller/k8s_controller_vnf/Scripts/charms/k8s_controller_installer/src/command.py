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
            # return False

      unit_status = ActiveStatus(f"<{component}> completed with success")
      return True
