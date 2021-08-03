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
import uuid

from glazier.lib import constants
from glazier.lib import registry
from glazier.lib import winpe
import yaml

from gwinpy.wmi import hw_info


class Error(Exception):
  pass


def _generate_id() -> str:
  """Generate the image identifier.

  Returns:
    The image identifier as a string.
  """
  hw = hw_info.HWInfo()
  return ('%s-%s' %
          (str(hw.BiosSerial()), str(uuid.uuid4())[:7])).upper()


def _set_id() -> str:
  """Set the image id registry key."""
  image_id = _generate_id()
  try:
    registry.set_value('image_id', image_id, path=constants.REG_ROOT)
  except registry.Error as e:
    raise Error(e)
  return image_id


def _check_file() -> str:
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
        registry.set_value('image_id', image_id, path=constants.REG_ROOT)
        return image_id
      except registry.Error as e:
        raise Error(e)
      except KeyError as e:
        raise Error('Could not determine %s from file: %s.' % (e, path))
  else:
    raise Error('Could not locate build info file.')


def check_id() -> str:
  """Call set_id if image identifier is not set and in WinPE.

  Check build_info (dumped via buildinfodump) in host if image_id does
  not exist.

  Returns:
    Image identifier as a string if already set.
  """
  image_id = None
  try:
    image_id = registry.get_value('image_id', path=constants.REG_ROOT)
  except registry.Error as e:
    logging.error(str(e))

  if image_id:
    return image_id
  if winpe.check_winpe():
    return _set_id()

  return _check_file()
