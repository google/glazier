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
from glazier.lib import cache
from glazier.lib import powershell
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


class PSScript(BaseAction):
  """Execute a Powershell script file."""

  def Run(self):
    script = self._args[0]
    ps_args = None
    if len(self._args) > 1:
      ps_args = self._args[1]
    ps = powershell.PowerShell(echo_off=True)
    c = cache.Cache()

    logging.info('Interpreting Powershell script: %s', script)
    try:
      script = c.CacheFromLine(script, self._build_info)
    except cache.CacheError as e:
      raise ActionError(e)

    try:
      ps.RunLocal(script, args=ps_args)
    except powershell.PowerShellError as e:
      raise ActionError('Failure executing Powershell script: %s' % e)

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 2:
      raise ValidationError('Invalid args length: %s' % self._args)
    self._TypeValidator(self._args[0], str)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], list)
