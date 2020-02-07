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
"""Tests for glazier.lib.registry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from glazier.lib import registry
import mock


class RegistryTest(absltest.TestCase):

  def setUp(self):
    super(RegistryTest, self).setUp()
    self.name = 'some_key'
    self.value = 'some_value'

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_get_value(self, reg):
    reg.return_value.GetKeyValue.return_value = self.value
    self.assertEqual(registry.get_value(self.name), self.value)
    reg.assert_called_with('HKLM')
    reg.return_value.GetKeyValue.assert_called_with(
        key_path=registry.constants.REG_ROOT,
        key_name=self.name,
        use_64bit=registry.constants.USE_REG_64)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_get_value_none(self, reg):
    reg.return_value.GetKeyValue.side_effect = registry.registry.RegistryError
    self.assertEqual(registry.get_value(self.name), None)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_set_value(self, mock_reg):
    registry.set_value(self.name, self.value)
    mock_reg.assert_called_with('HKLM')
    mock_reg.return_value.SetKeyValue.assert_has_calls([
        mock.call(
            key_path=registry.constants.REG_ROOT,
            key_name=self.name,
            key_value=self.value,
            key_type='REG_SZ',
            use_64bit=registry.constants.USE_REG_64),
    ])

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_set_value_error(self, reg):
    reg.return_value.SetKeyValue.side_effect = registry.registry.RegistryError
    self.assertRaises(registry.Error, registry.set_value, self.name, self.value)

if __name__ == '__main__':
  absltest.main()
