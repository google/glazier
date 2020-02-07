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
"""Wrapper library for gwinpy.registry functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Optional, Text

from glazier.lib import constants
from gwinpy.registry import registry


class Error(Exception):
  pass


def set_value(name: Text, value: Text,
              root: Optional[Text] = 'HKLM',
              path: Optional[Text] = constants.REG_ROOT,
              reg_type: Optional[Text] = 'REG_SZ',
              use_64bit: Optional[bool] = constants.USE_REG_64):
  r"""Set a registry value.

  Args:
    name: Registry value name.
    value: Registry value data.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    path: Registry key path. Defaults to constants.REG_ROOT.
    reg_type: Registry value type (REG_DWORD\REG_SZ). Defaults to REG_SZ.
    use_64bit: True for 64 bit registry. False for 32 bit.
    Defaults to constants.USE_REG_64.
  """
  try:
    reg = registry.Registry(root_key=root)
    reg.SetKeyValue(
        key_path=path,
        key_name=name,
        key_value=value,
        key_type=reg_type,
        use_64bit=use_64bit)
  except registry.RegistryError as e:
    raise Error(str(e))
