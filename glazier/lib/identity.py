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
"""Manipulate identity data during the image."""

import functools
import socket
from typing import Optional

from glazier.lib import interact
from glazier.lib import registry

from glazier.lib import constants


@functools.lru_cache()
def get_username() -> Optional[str]:
  """Gets the username from registry.

  Returns:
    username as a string.
  """
  return registry.get_value('Username', path=constants.REG_ROOT)


def set_username(username: Optional[str] = None,
                 prompt: Optional[str] = None) -> str:
  """Sets the username in the registry.

  Optionally prompts if there is no username supplied as a parameter.

  Args:
    username: Value to set as the username in registry.
    prompt: Custom string to append to username prompt.

  Returns:
    username: The determined username.

  Raises:
    RegistrySetError: Failed to set username in registry.
  """
  if not username:
    username = interact.GetUsername(prompt)
  registry.set_value('Username', username, path=constants.REG_ROOT)

  return username


@functools.lru_cache()
def get_hostname() -> Optional[str]:
  """Gets the hostname value from the registry.

  Returns:
    The hostname as a string, obtained from the registry value 'name'.
  """
  hostname = registry.get_value('Name', path=constants.REG_ROOT)
  return hostname.strip() if hostname else hostname


def set_hostname(hostname: Optional[str] = None) -> str:
  """Sets the hostname in the registry.

   Gets hostname from socket.hostname if no hostname is passed.

  Args:
    hostname: Value to set as the hostname in registry.

  Returns:
    hostname: The determined hostname.

  Raise:
    RegistrySetError: Failed to set hostname in registry.
  """
  if not hostname:
    hostname = socket.gethostname()

  hostname = hostname.strip()
  registry.set_value('Name', hostname, path=constants.REG_ROOT)

  return hostname
