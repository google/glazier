# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Ensure the device hardware is supported."""

import logging
import re

from glazier.lib.policies.base import BasePolicy
from glazier.lib.policies.base import ImagingPolicyException


class DeviceModel(BasePolicy):
  """Verify that the device hardware is supported."""

  PARTIAL_NOTICE = ("""
                    !!!!! Notice !!!!!

      The installer considers this hardware model obsolete or experimental (%s).

      The hardware you are using is not part of active inventory.
      While the installer may support this device, it is not being tested for
      compatibility.  There is a chance you may experience problems imaging.
      We recommend considering a hardware refresh before continuing.
      """)

  UNSUPPORTED_NOTICE = ("""
                    !!!!! Warning !!!!!

      The installer does not recognize this hardware model (%s).

      If you chose to continue, this will be an unsupported build.  The
      final install MAY BE BROKEN.  You should only continue if you are
      sure you know what you're doing.  When in doubt, contact support
      for assistance.
      """)

  def _ModelSupportPrompt(self, message: str, this_model: str) -> bool:
    """Prompts the user whether to halt an unsupported build.

    Args:
      message: A message to be displayed to the user.
      this_model: The hardware model that failed validation.

    Returns:
      true if the user wishes to proceed anyway, else false.
    """
    warning = message % this_model
    print(warning)
    answer = input('Do you still want to proceed (y/n)? ')
    answer_re = r'^[Yy](es)?$'
    if re.match(answer_re, answer):
      return True
    return False

  def Verify(self) -> bool:
    model = self._build_info.ComputerModel()
    logging.debug('Verifying hardware support tier for %s.', model)
    tier = self._build_info.SupportTier()
    if tier == 1:
      return True

    build_anyway = False
    if tier == 2:
      build_anyway = self._ModelSupportPrompt(self.PARTIAL_NOTICE, model)
    else:
      build_anyway = self._ModelSupportPrompt(self.UNSUPPORTED_NOTICE, model)

    if not build_anyway:
      raise ImagingPolicyException(
          'User chose not to continue with current model.')
    logging.info('User chose to continue with partial or unsupported build.')
    return build_anyway


class BannedPlatform(BasePolicy):

  def Verify(self):
    raise ImagingPolicyException(
        'Windows cannot be installed on this platform.')
