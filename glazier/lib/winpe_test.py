# Lint as: python3
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
"""Tests for glazier.lib.winpe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from glazier.lib import winpe
import mock


class WinPETest(absltest.TestCase):

  @mock.patch.object(winpe.registry, 'Registry', autospec=True)
  def testCheckWinPE(self, reg):
    # WinPE
    reg.return_value.GetKeyValue.return_value = 'WindowsPE'
    self.assertEqual(winpe.check_winpe(), True)
    reg.assert_called_with('HKLM')
    reg.return_value.GetKeyValue.assert_called_with(
        key_path=winpe.constants.WINPE_KEY,
        key_name=winpe.constants.WINPE_VALUE,
        use_64bit=winpe.constants.USE_REG_64)

    # Host
    reg.return_value.GetKeyValue.return_value = 'Enterprise'
    self.assertEqual(winpe.check_winpe(), False)

    # RegistryError
    reg.return_value.GetKeyValue.side_effect = winpe.registry.RegistryError
    self.assertRaises(winpe.Error, winpe.check_winpe)

if __name__ == '__main__':
  absltest.main()
