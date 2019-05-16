# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Action for running Googet commands with arguments."""

import logging
from glazier.lib import googet
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


# TODO(b/132087331): Add Support for multiple installs
class GoogetInstall(BaseAction):
  """Execute a Googet install command."""

  # TODO(b/132083921): Add support path transforms
  def Run(self):
    try:
      # Default to just the package being required
      if len(self._args) > 1:
        flags = self._args[1]
      else:
        flags = None

      if len(self._args) > 2:
        path = self._args[2]
      else:
        path = None

      logging.info('Invoking Googet with args %s', self._args)
      install = googet.GoogetInstall()
      install.LaunchGooget(pkg=self._args[0],
                           build_info=self._build_info,
                           path=path,
                           flags=flags)
    except googet.Error as e:
      raise ActionError("Failure executing Googet command with error: '%s'" %
                        e)
    except IndexError:
      raise ActionError("Unable to access all required arguments in command "
                        "'%s'" % str(self._args))

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 1 <= len(self._args) <= 3:
      raise ValidationError("Invalid Googet args '%s' with length of "
                            "'%d'" % (self._args, len(self._args)))
    self._TypeValidator(self._args[0], str)  # Package
    self._TypeValidator(self._args[1], str)  # Flags
    self._TypeValidator(self._args[2], str)  # Path
