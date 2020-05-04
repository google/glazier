# Lint as: python3
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

"""Actions for running Powershell scripts and commands."""

import logging
from typing import List, Optional, Text
from glazier.lib import cache
from glazier.lib import powershell
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import RestartEvent
from glazier.lib.actions.base import ValidationError


class PSScript(BaseAction):
  """Execute a Powershell script file."""

  def Run(self):
    script: Text = self._args[0]
    ps_args: Optional[List[Text]] = []
    success_codes: Optional[List[int]] = [0]
    reboot_codes: Optional[List[int]] = []
    restart_retry: Optional[bool] = False
    if len(self._args) > 1:
      ps_args = self._args[1]
    if len(self._args) > 2:
      success_codes = self._args[2]
    if len(self._args) > 3:
      reboot_codes = self._args[3]
    if len(self._args) > 4:
      restart_retry = self._args[4]

    ps = powershell.PowerShell()
    c = cache.Cache()

    logging.info('Interpreting Powershell script: %s', script)
    try:
      script = c.CacheFromLine(script, self._build_info)
    except cache.CacheError as e:
      raise ActionError(e)

    try:
      result = ps.RunLocal(script, ps_args, success_codes + reboot_codes)
    except powershell.PowerShellError as e:
      raise ActionError(str(e))

    if result in reboot_codes:
      raise RestartEvent('Restart triggered by exit code %d' % result, 5,
                         retry_on_restart=restart_retry)
    elif result not in success_codes:
      raise ActionError('Script returned invalid exit code %d' % result)

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 5:
      raise ValidationError('Invalid args length: %s' % self._args)
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


class PSCommand(BaseAction):
  """Execute a Powershell command."""

  def Run(self):
    command: List[Text] = self._args[0].split()
    success_codes: Optional[List[int]] = [0]
    reboot_codes: Optional[List[int]] = []
    restart_retry: Optional[bool] = False
    if len(self._args) > 1:
      success_codes = self._args[1]
    if len(self._args) > 2:
      reboot_codes = self._args[2]
    if len(self._args) > 3:
      restart_retry = self._args[3]

    ps = powershell.PowerShell()

    try:
      result = ps.RunCommand(command, success_codes + reboot_codes)
    except powershell.PowerShellError as e:
      raise ActionError(str(e))

    if result in reboot_codes:
      raise RestartEvent(
          'Restart triggered by exit code %d' % result,
          5,
          retry_on_restart=restart_retry)
    elif result not in success_codes:
      raise ActionError('Command returned invalid exit code %d' % result)

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 4:
      raise ValidationError('Invalid args length: %s' % self._args)
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
