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

"""Actions for interacting with the company domain."""

from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError
from glazier.lib import domain_join


class DomainJoin(BaseAction):
  """Create an imaging timer."""

  def Run(self):
    method = str(self._args[0])
    domain = str(self._args[1])
    ou = None
    if len(self._args) > 2:
      ou = str(self._args[2])
    joiner = domain_join.DomainJoin(method, domain, ou)
    try:
      joiner.JoinDomain()
    except domain_join.DomainJoinError as e:
      raise ActionError('Unable to complete domain join.') from e

  def Validate(self):
    self._ListOfStringsValidator(self._args, length=2, max_length=3)
    if self._args[0] not in domain_join.AUTH_OPTS:
      raise ValidationError(f'Invalid join method: {self._args[0]}')
