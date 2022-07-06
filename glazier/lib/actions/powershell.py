# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Actions for running PowerShell scripts and commands."""

import logging
from typing import List
from glazier.lib import cache
from glazier.lib import events
from glazier.lib import powershell
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


class PSScript(BaseAction):
  """Execute a PowerShell script file."""

  def Run(self):
    script: str = self._args[0]
    ps_args: List[str] = []
    success_codes: List[int] = [0]
    reboot_codes: List[int] = []
    restart_retry: bool = False
    shell: bool = False
    log: bool = True
    if len(self._args) > 1:
      ps_args = self._args[1]
    if len(self._args) > 2:
      success_codes = self._args[2]
    if len(self._args) > 3:
      reboot_codes = self._args[3]
    if len(self._args) > 4:
      restart_retry = self._args[4]
    if len(self._args) > 5:
      shell = self._args[5]
    if len(self._args) > 6:
      log = self._args[6]

    logging.info('Interpreting PowerShell script: %s', script)
    try:
      script = cache.Cache().CacheFromLine(script, self._build_info)  # pytype: disable=annotation-type-mismatch
    except cache.Error as e:
      raise ActionError() from e

    try:
      result = powershell.PowerShell(shell, log).RunLocal(
          script, ps_args, success_codes + reboot_codes)
    except powershell.Error as e:
      raise ActionError() from e

    if result in reboot_codes:
      raise events.RestartEvent(
          'Restart triggered by exit code %d' % result, 5,
          retry_on_restart=restart_retry)
    elif result not in success_codes:
      raise ActionError(f'Script returned invalid exit code {result}')

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 7:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], str)
    if len(self._args) > 1:  # ps_args
      self._TypeValidator(self._args[1], list)
    if len(self._args) > 2:  # success codes
      self._TypeValidator(self._args[2], list)
      for arg in self._args[2]:
        self._TypeValidator(arg, int)
    if len(self._args) > 3:  # reboot codes
      self._TypeValidator(self._args[3], list)
      for arg in self._args[3]:
        self._TypeValidator(arg, int)
    if len(self._args) > 4:  # retry on restart
      self._TypeValidator(self._args[4], bool)
    if len(self._args) > 5:  # shell
      self._TypeValidator(self._args[5], bool)
    if len(self._args) > 6:  # log
      self._TypeValidator(self._args[6], bool)


class MultiPSScript(BaseAction):
  """Executes PSScript on multiple sets of scripts."""

  def Run(self):
    for arg in self._args:
      try:
        PSScript(arg, self._build_info).Run()
      except IndexError as e:
        raise ActionError(
            f'Unable to determine PowerShell scripts from {arg}') from e

  def Validate(self):
    try:
      self._TypeValidator(self._args, list)
    except ValidationError as e:
      raise ActionError() from e
    for arg in self._args:
      PSScript(arg, self._build_info).Validate()


class PSCommand(BaseAction):
  """Execute a PowerShell command."""

  def Run(self):
    command: List[str] = self._args[0].split()
    success_codes: List[int] = [0]
    reboot_codes: List[int] = []
    restart_retry: bool = False
    shell: bool = False
    log: bool = True
    if len(self._args) > 1:
      success_codes = self._args[1]
    if len(self._args) > 2:
      reboot_codes = self._args[2]
    if len(self._args) > 3:
      restart_retry = self._args[3]
    if len(self._args) > 4:
      shell = self._args[4]
    if len(self._args) > 5:
      log = self._args[5]

    # TODO(b/155776932): Remove once updated PowerShell is used in the image.
    # PSScript (which calls powershell.exe -File) does not accept non-string
    # parameters. Instead, if the command string starts with a PowerShell
    # script, cache it's location and run the script using powershell.exe
    # -Command. See link below for more context.
    # https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1#-file----filepath-args
    if command[0] and command[0].endswith('.ps1'):
      logging.info('Interpreting PowerShell script: %s', command[0])
      try:
        command[0] = cache.Cache().CacheFromLine(command[0], self._build_info)  # pytype: disable=container-type-mismatch
      except cache.Error as e:
        raise ActionError() from e

    try:
      # Exit $LASTEXITCODE is necessary because PowerShell.exe -Command only
      # exits 0 or 1 by default.
      result = powershell.PowerShell(shell, log).RunCommand(
          command + ['; exit $LASTEXITCODE'], success_codes + reboot_codes)
    except powershell.Error as e:
      raise ActionError() from e

    if result in reboot_codes:
      raise events.RestartEvent(
          'Restart triggered by exit code %d' % result, 5,
          retry_on_restart=restart_retry)
    elif result not in success_codes:
      raise ActionError(f'Command returned invalid exit code {result}')

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 6:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], str)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], list)
      for arg in self._args[1]:  # success codes
        self._TypeValidator(arg, int)
    if len(self._args) > 2:  # reboot codes
      self._TypeValidator(self._args[2], list)
      for arg in self._args[2]:
        self._TypeValidator(arg, int)
    if len(self._args) > 3:  # retry on restart
      self._TypeValidator(self._args[3], bool)
    if len(self._args) > 4:  # shell
      self._TypeValidator(self._args[4], bool)
    if len(self._args) > 5:  # log
      self._TypeValidator(self._args[5], bool)


class MultiPSCommand(BaseAction):
  """Executes PSCommand on multiple sets of commands."""

  def Run(self):
    for arg in self._args:
      try:
        PSCommand(arg, self._build_info).Run()
      except IndexError as e:
        raise ActionError(
            f'Unable to determine PowerShell commands from {arg}') from e

  def Validate(self):
    try:
      self._TypeValidator(self._args, list)
    except ValidationError as e:
      raise ActionError() from e
    for arg in self._args:
      PSCommand(arg, self._build_info).Validate()
