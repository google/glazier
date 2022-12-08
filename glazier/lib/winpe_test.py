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

from unittest import mock

from absl.testing import absltest
from glazier.lib import winpe


class WinPETest(absltest.TestCase):

  @mock.patch.object(winpe.registry, 'get_value', autospec=True)
  def test_check_winpe_true(self, mock_get_value):
    winpe.check_winpe.cache_clear()
    mock_get_value.return_value = 'WindowsPE'
    result = winpe.check_winpe()
    self.assertIsInstance(result, bool)
    self.assertTrue(result)

  @mock.patch.object(winpe.registry, 'get_value', autospec=True)
  def test_check_winpe_false(self, mock_get_value):
    winpe.check_winpe.cache_clear()
    mock_get_value.return_value = 'Enterprise'
    result = winpe.check_winpe()
    self.assertIsInstance(result, bool)
    self.assertFalse(result)


if __name__ == '__main__':
  absltest.main()
