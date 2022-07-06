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

"""Actions for interacting with the host system."""

import logging

from glazier.lib import events
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


class _PowerAction(BaseAction):
  """Validation for Power actions."""

  def Validate(self):
    self._TypeValidator(self._args, list)
    if len(self._args) not in [1, 2, 3]:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    if not isinstance(self._args[0], str) and not isinstance(self._args[0],
                                                             int):
      raise ValidationError(f'Invalid argument type: {self._args[0]}')
    if len(self._args) > 1 and not isinstance(self._args[1], str):
      raise ValidationError(f'Invalid argument type: {self._args[1]}')
    if len(self._args) > 2 and not isinstance(self._args[2], bool):
      raise ValidationError(f'Invalid argument type: {self._args[2]}')


class Reboot(_PowerAction):
  """Perform a host reboot."""

  def Run(self):
    timeout = str(self._args[0])
    reason = 'unspecified'
    pop_next = False
    if len(self._args) > 1:
      reason = str(self._args[1])
    if len(self._args) > 2:
      pop_next = bool(self._args[2])
    logging.info('Rebooting with a timeout of %s and a reason of %s', timeout,
                 reason)
    raise events.RestartEvent(reason, timeout=timeout, pop_next=pop_next)


class Shutdown(_PowerAction):
  """Perform a host shutdown."""

  def Run(self):
    timeout = str(self._args[0])
    reason = 'unspecified'
    pop_next = False
    if len(self._args) > 1:
      reason = str(self._args[1])
    if len(self._args) > 2:
      pop_next = self._args[2]
    logging.info('Shutting down with a timeout of %s and a reason of %s',
                 timeout, reason)
    raise events.ShutdownEvent(reason, timeout=timeout, pop_next=pop_next)
