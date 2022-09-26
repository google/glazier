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

import logging
from typing import Optional, Union, List, Dict

from glazier.lib import constants
from glazier.lib import errors
from gwinpy.registry import registry


class Error(errors.GlazierError):
  pass


class RegistryWriteError(Error):

  def __init__(self,
               name: str,
               value: Union[str, int],
               path: Optional[str] = constants.REG_ROOT):
    message = (fr'Failed to write to registry: [{path}\{name} = {value}]')
    super().__init__(
        error_code=errors.ErrorCode.REGISTRY_WRITE_ERROR, message=message)


class RegistryDeleteError(Error):

  def __init__(self, name: str, path: Optional[str]):
    message = (fr'Failed to delete registry key: [{path}\{name}]')
    super().__init__(
        error_code=errors.ErrorCode.REGISTRY_DELETE_ERROR, message=message)


def get_value(name: str,
              root: Optional[str] = 'HKLM',
              path: Optional[str] = constants.REG_ROOT,
              use_64bit: Optional[bool] = constants.USE_REG_64,
              log: Optional[bool] = True) -> Optional[str]:
  r"""Get a registry key value from registry.

  Args:
    name: Registry value name.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    path: Registry key path. Defaults to constants.REG_ROOT.
    use_64bit: True for 64 bit registry. False for 32 bit. Defaults to
      constants.USE_REG_64.
    log: Log the registry operation to the standard logger. Defaults to True.

  Returns:
    The registry value a string or None.
  """
  try:
    reg = registry.Registry(root_key=root)
    value = reg.GetKeyValue(key_path=path, key_name=name, use_64bit=use_64bit)
    if value:
      if log:
        logging.debug(r'Got registry value: %s:\%s\%s = %s.', root, path, name,
                      value)
      return value
  except registry.RegistryError as e:
    logging.warning(str(e))
  return None


def set_value(name: str,
              value: Union[str, int],
              root: Optional[str] = 'HKLM',
              path: Optional[str] = constants.REG_ROOT,
              reg_type: Optional[str] = 'REG_SZ',
              use_64bit: Optional[bool] = constants.USE_REG_64,
              log: Optional[bool] = True):
  r"""Set a registry value.

  Args:
    name: Registry value name.
    value: Registry value data.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    path: Registry key path. Defaults to constants.REG_ROOT.
    reg_type: Registry value type (REG_DWORD\REG_SZ). Defaults to REG_SZ.
    use_64bit: True for 64 bit registry. False for 32 bit. Defaults to
      constants.USE_REG_64.
    log: Log the registry operation to the standard logger. Defaults to True.
  """
  try:
    reg = registry.Registry(root_key=root)
    reg.SetKeyValue(
        key_path=path,
        key_name=name,
        key_value=value,
        key_type=reg_type,
        use_64bit=use_64bit)
    if log:
      logging.debug(r'Set registry value: %s:\%s\%s = %s', root, path, name,
                    str(value))
  except registry.RegistryError as e:
    raise RegistryWriteError(name, value, path) from e


def get_values(path: str,
               root: Optional[str] = 'HKLM',
               use_64bit: Optional[bool] = constants.USE_REG_64,
               log: Optional[bool] = True) -> Optional[List[str]]:
  r"""Gets a list of registry values.

  Args:
    path: Registry key path to enumerate from.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    use_64bit: True for 64 bit registry. False for 32 bit. Defaults to
      constants.USE_REG_64.
    log: Log the registry operation to the standard logger. Defaults to True.

  Returns:
    The registry values as a List of strings or None.
  """
  try:
    reg = registry.Registry(root_key=root)
    values = reg.GetRegKeys(key_path=path, use_64bit=use_64bit)
    if values:
      if log:
        logging.debug(r'Registry keys under %s:\%s = %s.', root, path, values)
      return values
  except registry.RegistryError as e:
    logging.warning(str(e))
    return None


def get_keys_and_values(path: str,
                        root: Optional[str] = 'HKLM',
                        use_64bit: Optional[bool] = constants.USE_REG_64,
                        log: Optional[bool] = True) -> Optional[Dict[str, str]]:
  r"""Gets a dict of registry keys and values.

  Args:
    path: Registry key path to enumerate from.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    use_64bit: True for 64 bit registry. False for 32 bit. Defaults to
      constants.USE_REG_64.
    log: Log the registry operation to the standard logger. Defaults to True.

  Returns:
    The registry keys and values as a Dict of strings or None.
  """
  keys_and_values = {}
  try:
    reg = registry.Registry(root_key=root)
    result = reg.GetRegKeysAndValues(key_path=path, use_64bit=use_64bit)
    if result:
      if log:
        logging.debug(r'Registry keys under %s:\%s...', root, path)
        for k, v, _ in result:
          logging.debug('%s = %s', k, v)
          keys_and_values[k] = v
      return keys_and_values
  except registry.RegistryError as e:
    logging.warning(str(e))
    return None


def remove_value(name: str,
                 root: Optional[str] = 'HKLM',
                 path: Optional[str] = constants.REG_ROOT,
                 use_64bit: Optional[bool] = constants.USE_REG_64,
                 log: Optional[bool] = True):
  r"""Remove a registry value.

  Args:
    name: Registry value name.
    root: Registry root (HKCR\HKCU\HKLM\HKU). Defaults to HKLM.
    path: Registry key path. Defaults to constants.REG_ROOT.
    use_64bit: True for 64 bit registry. False for 32 bit. Defaults to
      constants.USE_REG_64.
    log: Log the registry operation to the standard logger. Defaults to True.
  """
  try:
    reg = registry.Registry(root_key=root)
    reg.RemoveKeyValue(key_path=path, key_name=name, use_64bit=use_64bit)
    if log:
      logging.debug(r'Removed registry key: %s:\%s\%s', root, path, name)
  except registry.RegistryError as e:
    if e.errno == 2:
      logging.warning(r'Failed to delete non-existant registry key: %s:\%s\%s',
                      root, path, name)
    else:
      raise RegistryDeleteError(name, path) from e
