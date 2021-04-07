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

from glazier.lib import splice
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction


class SpliceDomainJoin(BaseAction):
  """Join a machine to the domain via Splice."""

  def Run(self):
    self._splice = splice.Splice()
    try:
      self._splice.domain_join()
    except splice.Error as e:
      raise ActionError(str(e))
