# Copyright 2022 Google Inc. All Rights Reserved.
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

"""Ensure the machine bios is up-to-date."""

from glazier.lib.policies.base import BasePolicy
from glazier.lib.policies.base import ImagingPolicyException

_VERSION = 'S07KT26A'


class BIOSVersion(BasePolicy):

  def Verify(self):
    version = self._build_info.BIOSVersion()
    if version < _VERSION:
      raise ImagingPolicyException(
          'Please update the BIOS, then reimage this system.')
