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
"""Utility library for getting/setting registry data."""

import functools
import logging
import socket
from typing import Optional, Text

from glazier.lib import interact
from glazier.lib import registry


class Error(Exception):
  pass


@functools.lru_cache()
def get_username() -> Optional[Text]:
  """Gets the username from registry.

  Returns:
    username as a string.
  """
  try:
    return registry.get_value('Username')
  except registry.Error as e:
    logging.error(str(e))


def set_username(username: Optional[Text] = None,
                 prompt: Optional[Text] = None) -> Text:
  """Sets the username in the registry.

  Optionally prompts if there is no username supplied as a parameter.

  Args:
    username: Value to set as the username in registry.
    prompt: Custom string to append to username prompt.

  Returns:
    username: The determined username.

  Raises:
    Error: Failed to set username in registry.
  """
  if not username:
    username = interact.GetUsername(prompt)
  try:
    registry.set_value('Username', username)
  except registry.Error as e:
    raise Error(str(e))

  return username


@functools.lru_cache()
def get_hostname() -> Optional[Text]:
  """Gets the hostname value from the registry.

  Returns:
    The hostname as a string, obtained from the registry value 'name'.
  """
  try:
    hostname = registry.get_value('Name')
  except registry.Error as e:
    logging.error(str(e))
  else:
    return hostname.strip() if hostname else hostname


def set_hostname(hostname: Optional[Text] = None) -> Text:
  """Sets the hostname in the registry.

   Gets hostname from socket.hostname if no hostname is passed.

  Args:
    hostname: Value to set as the hostname in registry.

  Returns:
    hostname: The determined hostname.

  Raise:
    Error: Failed to set hostname in registry.
  """
  if not hostname:
    hostname = socket.gethostname()

  hostname = hostname.strip()

  try:
    registry.set_value('Name', hostname)
  except registry.Error as e:
    raise Error(str(e))

  return hostname


@functools.lru_cache()
def check_winpe() -> bool:
  """Verify image environment is WinPE or Host.

  Returns:
    True for WinPE, else False.
  """
  try:
    value = registry.get_value(
        'EditionID',
        'HKLM',
        r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
        log=False)
    if value == 'WindowsPE':
      return True
    else:
      return False
  except registry.Error as e:
    raise Error('Failed to detect image environment (%s)' % str(e))
