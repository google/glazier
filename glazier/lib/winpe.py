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

import functools
import os

from glazier.lib import constants
from glazier.lib import errors
from glazier.lib import execute
from glazier.lib import registry


class UtilError(errors.GlazierError):

  def __init__(self, message: str):
    super().__init__(error_code=errors.ErrorCode.WPEUTIL_ERROR, message=message)


@functools.lru_cache()
def check_winpe() -> bool:
  """Verify image environment is WinPE or Host.

  Returns:
    True for WinPE, else False.
  """
  value = registry.get_value(
      'EditionID', 'HKLM', r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
      log=False)
  return bool(value == 'WindowsPE')


WPEUTIL = os.path.join(constants.WINPE_SYSTEM32, 'wpeutil.exe')


def disable_firewall():
  try:
    execute.check_output(WPEUTIL, args=['DisableFirewall'], timeout=20)
  except execute.Error as e:
    raise UtilError(
        message='wpeutil disablefirewall failed with %s' % e.message
    ) from e


def enable_firewall():
  try:
    execute.check_output(WPEUTIL, args=['EnableFirewall'], timeout=20)
  except execute.Error as e:
    raise UtilError(
        message='wpeutil enablefirewall failed with %s' % e.message
    ) from e
