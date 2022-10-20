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

import logging

from unittest import mock

from absl.testing import absltest
from glazier.lib import registry
from glazier.lib import test_utils
from gwinpy.registry import registry as gwinpy_registry
from glazier.lib import constants


class RegistryTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(RegistryTest, self).setUp()
    self.name = 'some_key'
    self.value = 'some_value'
    self.type = mock.ANY

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_value(self, mock_registry):
    mock_registry.return_value.GetKeyValue.return_value = self.value
    self.assertEqual(registry.get_value(self.name), self.value)
    mock_registry.assert_called_with('HKLM')
    mock_registry.return_value.GetKeyValue.assert_called_with(
        key_path=constants.REG_ROOT,
        key_name=self.name,
        use_64bit=constants.USE_REG_64)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_value_none(self, mock_registry):
    mock_registry.return_value.GetKeyValue.side_effect = (
        gwinpy_registry.RegistryError)
    self.assertIsNone(registry.get_value(self.name))

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'debug', autospec=True)
  def test_get_value_silent(self, mock_debug, mock_registry):
    mock_registry.return_value.GetKeyValue.return_value = self.value
    registry.get_value(self.name, log=False)
    self.assertFalse(mock_debug.called)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_values(self, mock_registry):
    mock_registry.return_value.GetRegKeys.return_value = self.value
    self.assertEqual(registry.get_values(self.name), self.value)
    mock_registry.assert_called_with('HKLM')
    mock_registry.return_value.GetRegKeys.assert_called_with(
        key_path=self.name, use_64bit=constants.USE_REG_64)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_values_none(self, mock_registry):
    mock_registry.return_value.GetRegKeys.side_effect = (
        gwinpy_registry.RegistryError)
    self.assertIsNone(registry.get_values(self.name))

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'debug', autospec=True)
  def test_get_values_silent(self, mock_debug, mock_registry):
    mock_registry.return_value.GetRegKeys.return_value = self.value
    registry.get_values(self.name, log=False)
    self.assertFalse(mock_debug.called)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_keys_and_values(self, mock_registry):
    mock_registry.return_value.GetRegKeysAndValues.return_value = [
        (self.name, self.value, self.type), ('name2', 'value2', self.type)
    ]
    self.assertEqual(
        registry.get_keys_and_values(self.name), {
            self.name: self.value,
            'name2': 'value2'
        })
    mock_registry.assert_called_with('HKLM')
    mock_registry.return_value.GetRegKeysAndValues.assert_called_with(
        key_path=self.name, use_64bit=constants.USE_REG_64)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_get_keys_and_values_none(self, mock_registry):
    mock_registry.return_value.GetRegKeysAndValues.side_effect = (
        gwinpy_registry.RegistryError)
    self.assertIsNone(registry.get_keys_and_values(self.name))

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'debug', autospec=True)
  def test_get_keys_and_values_silent(self, mock_debug, mock_registry):
    mock_registry.return_value.GetRegKeysAndValues.return_value = self.value
    registry.get_keys_and_values(self.name, log=False)
    self.assertFalse(mock_debug.called)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_set_value(self, mock_registry):
    registry.set_value(self.name, self.value)
    mock_registry.assert_called_with('HKLM')
    mock_registry.return_value.SetKeyValue.assert_has_calls([
        mock.call(
            key_path=constants.REG_ROOT,
            key_name=self.name,
            key_value=self.value,
            key_type='REG_SZ',
            use_64bit=constants.USE_REG_64),
    ])

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_set_value_error(self, mock_registry):
    mock_registry.return_value.SetKeyValue.side_effect = (
        gwinpy_registry.RegistryError)
    with self.assert_raises_with_validation(registry.Error):
      registry.set_value(self.name, self.value)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'debug', autospec=True)
  def test_set_value_silent(self, mock_debug, unused_registry):
    registry.set_value(self.name, self.value, log=False)
    self.assertFalse(mock_debug.called)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_remove_value(self, mock_registry):
    registry.remove_value(self.name)
    mock_registry.assert_called_with('HKLM')
    mock_registry.return_value.RemoveKeyValue.assert_has_calls([
        mock.call(
            key_path=constants.REG_ROOT,
            key_name=self.name,
            use_64bit=constants.USE_REG_64),
    ])

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'warning', autospec=True)
  def test_remove_value_not_found(self, mock_warning, mock_registry):
    mock_registry.return_value.RemoveKeyValue.side_effect = (
        gwinpy_registry.RegistryError('Test', errno=2))
    registry.remove_value(self.name)
    mock_warning.assert_called_with(
        r'Failed to delete non-existant registry key: '
        r'%s:\%s\%s', 'HKLM', constants.REG_ROOT, self.name)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  def test_remove_value_error(self, mock_registry):
    mock_registry.return_value.RemoveKeyValue.side_effect = (
        gwinpy_registry.RegistryError)
    with self.assert_raises_with_validation(registry.Error):
      registry.remove_value(self.name)

  @mock.patch.object(gwinpy_registry, 'Registry', autospec=True)
  @mock.patch.object(logging, 'debug', autospec=True)
  def test_remove_value_silent(self, mock_debug, unused_registry):
    registry.remove_value(self.name, log=False)
    self.assertFalse(mock_debug.called)


if __name__ == '__main__':
  absltest.main()
