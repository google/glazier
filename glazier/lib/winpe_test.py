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

  @mock.patch.object(winpe.registry, 'get_value', autospec=True)
  def test_check_winpe_true(self, gv):
    gv.return_value = 'WindowsPE'
    self.assertEqual(winpe.check_winpe(), True)

  @mock.patch.object(winpe.registry, 'get_value', autospec=True)
  def test_check_winpe_false(self, gv):
    gv.return_value = 'Enterprise'
    self.assertEqual(winpe.check_winpe(), False)

  @mock.patch.object(winpe.registry, 'get_value', autospec=True)
  def test_check_winpe_error(self, gv):
    gv.side_effect = winpe.registry.Error
    self.assertRaises(winpe.Error, winpe.check_winpe)

if __name__ == '__main__':
  absltest.main()
