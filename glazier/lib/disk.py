# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Manipulates disk information."""

import logging
import shutil

from glazier.lib import constants
from glazier.lib import registry


class Error(Exception):
  pass


def get_disk_space():
  """Get the total, used, and free disk space.

  Returns:
    A tuple of total, used, and free disk space on main OS partition.
  """
  try:
    return shutil.disk_usage('/')
  except FileNotFoundError:
    logging.error(
        'Failed to locate OS partition. Could not determine disk size.')


def set_disk_space() -> None:
  """Sets disk space values in the registry.

  This is particularly useful for identifying how much disk space is used by
  your hosts during provisioning to inform decisions around how much disk space
  is actually needed.
  """
  space = get_disk_space()

  for k, v in space._asdict().items():
    space_in_gb = v // (2**30)
    try:
      registry.set_value(
          f'{k}_disk_space', f'{space_in_gb} GB', path=constants.REG_ROOT)
    except registry.Error as e:
      logging.error('Failed to write %s_disk_space to registry: %s', k, str(e))
