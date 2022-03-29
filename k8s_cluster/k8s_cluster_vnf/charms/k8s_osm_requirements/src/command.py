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
      
      self.result: str = ''
      self.error: str = ''


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

   def unit_run_command(self, component: str, logger: Logger, proxy: SSHProxy, unit_status: StatusBase) -> None:
      for i in range(len(self.commands)):
         current_command = self.commands[i]
         
         unit_status = MaintenanceStatus(current_command.initial_status)
         try:
            current_command.result, current_command.error = proxy.run(current_command.cmd)
            logger.info(f"Status: {current_command.ok_status}; Output: {current_command.result}; Errors: {current_command.error}")
            unit_status = MaintenanceStatus(current_command.ok_status)
         except Exception as e:
            logger.error(f"[{current_command.error_status}] failed <{e}>. Stderr: <{current_command.error}>")
            unit_status = BlockedStatus(current_command.error_status)
            raise Exception(f"[Unable to <{component}>]; Status: <{current_command.error_status}>; Action failed <{e}>; Stderr: <{current_command.error}>")

      unit_status = ActiveStatus(f"<{component}> completed with success")
