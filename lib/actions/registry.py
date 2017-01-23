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

from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from gwinpy.registry import registry


class RegAdd(BaseAction):
  """Add a new registry key."""

  def Run(self):
    use_64bit = True
    if len(self._args) > 5:
      use_64bit = self._args[5]

    try:
      reg = registry.Registry(root_key=self._args[0])
      reg.SetKeyValue(key_path=self._args[1],
                      key_name=self._args[2],
                      key_value=self._args[3],
                      key_type=self._args[4],
                      use_64bit=use_64bit)
    except registry.RegistryError as e:
      raise ActionError(str(e))
    except IndexError:
      raise ActionError('Unable to access all required arguments. [%s]' %
                        str(self._args))
