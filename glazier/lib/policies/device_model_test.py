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
"""Tests for glazier.lib.policies.device_model."""

from unittest import mock
from absl.testing import absltest
from glazier.lib import test_utils
from glazier.lib.policies import device_model


class DeviceModelTest(test_utils.GlazierTestCase):

  @mock.patch('builtins.input', autospec=True)
  @mock.patch('builtins.print', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_verify(self, mock_buildinfo, mock_print, mock_input):
    dm = device_model.DeviceModel(mock_buildinfo)

    # Tier1
    dm._build_info.SupportTier.return_value = 1
    self.assertTrue(dm.Verify())

    # Tier 2
    mock_input.return_value = 'yes'
    dm._build_info.ComputerModel.return_value = 'Test Workstation'
    dm._build_info.SupportTier.return_value = 2
    self.assertTrue(dm.Verify())
    mock_print.assert_called_with(device_model.DeviceModel.PARTIAL_NOTICE %
                                  'Test Workstation')

    # Unsupported: Continue
    mock_input.return_value = 'Y'
    dm._build_info.SupportTier.return_value = 0
    self.assertTrue(dm.Verify())
    mock_print.assert_called_with(device_model.DeviceModel.UNSUPPORTED_NOTICE %
                                  'Test Workstation')

    # Unsupported: Abort
    mock_input.return_value = 'n'
    with self.assert_raises_with_validation(
        device_model.ImagingPolicyException):
      dm.Verify()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_banned_platform(self, mock_buildinfo):
    bp = device_model.BannedPlatform(mock_buildinfo)
    with self.assert_raises_with_validation(
        device_model.ImagingPolicyException):
      bp.Verify()


if __name__ == '__main__':
  absltest.main()
