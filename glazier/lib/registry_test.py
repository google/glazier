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
  @mock.patch.object(registry.logging, 'debug', autospec=True)
  def test_get_value_silent(self, d, reg):
    reg.return_value.GetKeyValue.return_value = self.value
    registry.get_value(self.name, log=False)
    self.assertFalse(d.called)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_set_value(self, reg):
    registry.set_value(self.name, self.value)
    reg.assert_called_with('HKLM')
    reg.return_value.SetKeyValue.assert_has_calls([
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

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  @mock.patch.object(registry.logging, 'debug', autospec=True)
  def test_set_value_silent(self, d, unused_reg):
    registry.set_value(self.name, self.value, log=False)
    self.assertFalse(d.called)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_remove_value(self, reg):
    registry.remove_value(self.name)
    reg.assert_called_with('HKLM')
    reg.return_value.RemoveKeyValue.assert_has_calls([
        mock.call(
            key_path=registry.constants.REG_ROOT,
            key_name=self.name,
            use_64bit=registry.constants.USE_REG_64),
    ])

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  @mock.patch.object(registry.logging, 'warning', autospec=True)
  def test_remove_value_not_found(self, w, reg):
    reg.return_value.RemoveKeyValue.side_effect = \
        registry.registry.RegistryError('Test', errno=2)
    registry.remove_value(self.name)
    w.assert_called_with(r'Failed to delete non-existant registry key: '
                         r'%s:\%s\%s', 'HKLM', registry.constants.REG_ROOT,
                         self.name)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def test_remove_value_error(self, reg):
    reg.return_value.RemoveKeyValue.side_effect = registry.registry.RegistryError
    self.assertRaises(registry.Error, registry.remove_value, self.name)

  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  @mock.patch.object(registry.logging, 'debug', autospec=True)
  def test_remove_value_silent(self, d, unused_reg):
    registry.remove_value(self.name, log=False)
    self.assertFalse(d.called)

if __name__ == '__main__':
  absltest.main()
