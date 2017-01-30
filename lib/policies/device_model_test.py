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

from glazier.lib.policies import device_model
import mock
from google.apputils import basetest


class DeviceModelTest(basetest.TestCase):

  @mock.patch('__builtin__.raw_input', autospec=True)
  @mock.patch('__builtin__.print', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo',
              autospec=True)
  def testVerify(self, build_info, user_out, user_in):
    dm = device_model.DeviceModel(build_info)

    # Tier1
    dm._build_info.SupportTier.return_value = 1
    self.assertTrue(dm.Verify())

    # Tier 2
    user_in.return_value = 'yes'
    dm._build_info.ComputerModel.return_value = 'Test Workstation'
    dm._build_info.SupportTier.return_value = 2
    self.assertTrue(dm.Verify())
    user_out.assert_called_with(device_model._PARTIAL_NOTICE %
                                'Test Workstation')
    # Unsupported: Continue
    user_in.return_value = 'Y'
    dm._build_info.SupportTier.return_value = 0
    self.assertTrue(dm.Verify())
    user_out.assert_called_with(device_model._UNSUPPORTED_NOTICE %
                                'Test Workstation')
    # Unsupported: Abort
    user_in.return_value = 'n'
    self.assertRaises(device_model.ImagingPolicyException, dm.Verify)

  @mock.patch('glazier.lib.buildinfo.BuildInfo',
              autospec=True)
  def testBannedPlatform(self, build_info):
    bp = device_model.BannedPlatform(build_info)
    self.assertRaises(device_model.ImagingPolicyException,
                      bp.Verify)


if __name__ == '__main__':
  basetest.main()
