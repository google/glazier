# Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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

"""Actions to run Splice domain join during the image."""

from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError
from glazier.lib import splice


class SpliceDomainJoin(BaseAction):
  """Join a machine to the domain via Splice."""

  def Run(self):
    self._splice = splice.Splice()

    max_retries: int
    unattended: bool
    fallback: bool
    generator: str

    if self._args:
      max_retries = int(self._args[0])
    else:
      max_retries = 5
    if len(self._args) > 1:
      unattended = bool(self._args[1])
    else:
      unattended = True
    if len(self._args) > 2:
      fallback = bool(self._args[2])
    else:
      fallback = True
    if len(self._args) > 3:
      generator = str(self._args[3])
    else:
      generator = ''
    try:
      self._splice.domain_join(max_retries, unattended, fallback, generator)
    except splice.Error as e:
      raise ActionError(e) from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    if not 0 <= len(self._args) <= 3:
      raise ValidationError('Invalid args length: %s' % self._args)
    if self._args:
      self._TypeValidator(self._args[0], int)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], bool)
    if len(self._args) > 2:
      self._TypeValidator(self._args[2], bool)
