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

"""Actions for managing the host registry."""
# do not remove: internal placeholder 1
from glazier.lib import constants
from glazier.lib import registry
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


class RegAdd(BaseAction):
  """Add a new registry key."""

  def Run(self):

    use_64bit = constants.USE_REG_64
    if len(self._args) > 5:
      use_64bit = self._args[5]

    try:
      registry.set_value(self._args[2], self._args[3],
                         self._args[0], self._args[1],
                         self._args[4], use_64bit=use_64bit)
    except registry.Error as e:
      raise ActionError() from e
    except IndexError as e:
      raise ActionError(
          f'Unable to access all required arguments: {self._args}') from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 5 <= len(self._args) <= 6:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], str)  # Root key
    self._TypeValidator(self._args[1], str)  # Key path
    self._TypeValidator(self._args[2], str)  # Key name
    if self._args[4] == 'REG_DWORD':  # Key value
      self._TypeValidator(self._args[3], int)
    else:
      self._TypeValidator(self._args[3], str)
    self._TypeValidator(self._args[4], str)  # Key type
    if self._args[4] not in ['REG_DWORD', 'REG_SZ']:
      raise ValidationError(f'Unsupported Key type passed: {self._args[4]}')
    if len(self._args) > 5:  # Use 64bit Registry
      self._TypeValidator(self._args[5], bool)


class MultiRegAdd(BaseAction):
  """Perform RegAdd on multiple sets of registry entries."""

  def Run(self):
    try:
      for arg in self._args:
        ra = RegAdd(arg, self._build_info)
        ra.Run()
    except IndexError as e:
      raise ActionError(
          f'Unable to determine registry sets from {self._args}.') from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    for arg in self._args:
      ra = RegAdd(arg, self._build_info)
      ra.Validate()


class RegDel(BaseAction):
  """Delete a registry key."""

  def Run(self):
    use_64bit = True

    if len(self._args) > 3:
      use_64bit = self._args[3]

    try:
      registry.remove_value(self._args[2], self._args[0],
                            self._args[1], use_64bit=use_64bit)
    except registry.Error as e:
      raise ActionError() from e
    except IndexError as e:
      message = f'Unable to access all required arguments: {self._args}'
      raise ActionError(message) from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 3 <= len(self._args) <= 4:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], str)  # Root key
    self._TypeValidator(self._args[1], str)  # Key path
    self._TypeValidator(self._args[2], str)  # Key name
    if len(self._args) > 3:  # Use 64bit Registry
      self._TypeValidator(self._args[3], bool)


class MultiRegDel(BaseAction):
  """Perform RegDel on multiple sets of registry entries."""

  def Run(self):
    try:
      for arg in self._args:
        rd = RegDel(arg, self._build_info)
        rd.Run()
    except IndexError as e:
      raise ActionError(
          f'Unable to determine registry sets from {self._args}.') from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    for arg in self._args:
      rd = RegDel(arg, self._build_info)
      rd.Validate()
