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
from absl.testing import parameterized
from glazier.lib.policies import bios


class BIOSVersionTest(parameterized.TestCase):

  @parameterized.named_parameters(
      ('exact_match', 'S07KT26A'),
      ('newer_bios', 'S07KT26B'),
      ('older_bios', 'S07KT25A'),
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_verify(self, bios_version, mock_build_info):
    bv = bios.BIOSVersion(mock_build_info)
    bv._build_info.BIOSVersion.return_value = bios_version
    if bios_version < 'S07KT26A':
      self.assertRaises(bios.ImagingPolicyException, bv.Verify)
    else:
      self.assertIsNone(bv.Verify())

if __name__ == '__main__':
  absltest.main()
