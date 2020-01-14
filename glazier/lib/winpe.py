# Lint as: python3
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Encapsulates information pertaining to WinPE during the image."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from glazier.lib import constants
from gwinpy.registry import registry


class Error(Exception):
  pass


def check_winpe() -> bool:
  """Verify image environment is WinPE or Host.

  Returns:
    True for WinPE, else False.
  """
  try:
    reg = registry.Registry(root_key='HKLM')
    regkey = reg.GetKeyValue(
        key_path=constants.WINPE_KEY,
        key_name=constants.WINPE_VALUE,
        use_64bit=constants.USE_REG_64)
    if regkey == 'WindowsPE':
      return True
    else:
      return False
  except registry.RegistryError as e:
    raise Error("Could not read WinPE registry key '%s\\%s'. %s" %
                (constants.WINPE_KEY, constants.WINPE_VALUE, str(e)))
