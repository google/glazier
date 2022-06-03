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

"""Action for running GooGet commands with arguments."""

from glazier.lib import googet
from glazier.lib.actions.base import BaseAction

from glazier.lib import errors


class GooGetInstall(BaseAction):
  """Execute a GooGet install command."""

  # TODO(b/132083921): Add support path transforms
  def Run(self):
    for args in self._args:
      # Default to just the package being required
      if len(args) > 1:
        flags = args[1]
      else:
        flags = None

      if len(args) > 2:
        path = args[2]
      else:
        path = None

      if len(args) > 3:
        retries = int(args[3])
      else:
        retries = 5

      if len(args) > 4:
        sleep = int(args[4])
      else:
        sleep = 30

      try:
        install = googet.GooGetInstall()
        install.LaunchGooGet(pkg=args[0],
                             retries=retries,
                             sleep=sleep,
                             build_info=self._build_info,
                             path=path,
                             flags=flags)
      except errors.GooGetError as e:
        raise errors.ActionError(
            "Failure executing GooGet command: '%s'" % e) from e
      except IndexError as e:
        message = (
            "Unable to access all required arguments in command '%s'"
        ) % str(args)
        raise errors.ActionError(message) from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    for args in self._args:
      if not 1 <= len(args) <= 5:
        raise errors.ValidationError(
            "Invalid GooGet args '%s' with length of '%d'" % (args, len(args)))
      self._TypeValidator(args[0], str)  # Package
      if len(args) > 1:
        self._TypeValidator(args[1], list)  # Flags
      if len(args) > 2:
        self._TypeValidator(args[2], str)  # Path
      if len(args) > 3:
        self._TypeValidator(args[3], int)  # Retries
      if len(args) > 4:
        self._TypeValidator(args[4], int)  # Sleep interval
