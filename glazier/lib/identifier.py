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
import logging
import os
from typing import Optional, Text
import uuid

from glazier.lib import constants
from glazier.lib import winpe
from gwinpy.registry import registry
from gwinpy.wmi import hw_info

import yaml


class Error(Exception):
  pass


class ImageID(object):
  """Generate, log, and manage the unique image identifier."""

  def __init__(self):
    self._hw_info = hw_info.HWInfo()

  def _generate_id(self) -> Text:
    """Generate the image identifier.

    Returns:
      The image identifier as a string.
    """
    return ('%s-%s' %
            (str(self._hw_info.BiosSerial()), str(uuid.uuid4())[:7]))

  # TODO: Move to common registry wrapper lib.
  def _write_reg(self, name: Text, value: Text):
    """Writes a registry value.

    Args:
      name: Name of the registry key.
      value: Value of the registry key.
    """
    try:
      reg = registry.Registry(root_key='HKLM')
      reg.SetKeyValue(
          key_path=constants.REG_ROOT,
          key_name=name,
          key_value=value,
          key_type='REG_SZ',
          use_64bit=constants.USE_REG_64)
      logging.info('%s written to registry with value: %s.', name, value)
    except registry.RegistryError as e:
      raise Error(str(e))

  def _set_id(self) -> Text:
    """Set the image id registry key."""
    image_id = self._generate_id()
    self._write_reg('image_id', image_id)
    return image_id

  def _get_id(self) -> Optional[Text]:
    """Get the image ID from registry.

    Returns:
      The image identifier as a string or None.
    """
    try:
      reg = registry.Registry(root_key='HKLM')
      regkey = reg.GetKeyValue(
          key_path=constants.REG_ROOT,
          key_name='image_id',
          use_64bit=constants.USE_REG_64)
      if regkey:
        logging.info('Got image identifier from registry: %s.', regkey)
        return regkey
    except registry.RegistryError as e:
      logging.warning('Image identifier not found in registry: %s.', str(e))
    return None

  def _check_file(self) -> Text:
    """Call set_id if image identifier is not set and in WinPE.

    Returns:
      Image identifier as a string if already set.

    Raises:
      Error: Could not locate build info file.
      Error: Could not determine image identifier from file.
    """
    # First boot into host needs to grab image_id from buildinfo file.
    # It has not been written to registry yet.
    path = os.path.join(constants.SYS_CACHE, 'build_info.yaml')
    if os.path.exists(path):
      with open(path) as handle:
        try:
          input_config = yaml.safe_load(handle)
          image_id = input_config['BUILD']['image_id']
          self._write_reg('image_id', image_id)
          return image_id
        except KeyError as e:
          raise Error('Could not determine %s from file: %s.' % (e, path))
    else:
      raise Error('Could not locate build info file.')

  def check_id(self) -> Text:
    """Call set_id if image identifier is not set and in WinPE.

    Check build_info (dumped via buildinfodump) in host if image_id does
    not exist.

    Returns:
      Image identifier as a string if already set.
    """
    image_id = self._get_id()
    if image_id:
      return image_id

    if winpe.check_winpe():
      return self._set_id()

    return self._check_file()

