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

import functools
from glazier.lib import registry


@functools.lru_cache()
def check_winpe() -> bool:
  """Verify image environment is WinPE or Host.

  Returns:
    True for WinPE, else False.
  """
  value = registry.get_value(
      'EditionID', 'HKLM', r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
      log=False)
  if value == 'WindowsPE':
    return True
  else:
    return False
