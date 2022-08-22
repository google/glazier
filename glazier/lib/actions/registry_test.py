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
"""Tests for glazier.lib.actions.registry."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import constants
from glazier.lib import test_utils
from glazier.lib.actions import registry

ROOT = 'HKLM'
PATH = constants.REG_ROOT
NAME = 'some_name'
VALUE = 'some_data'
TYPE = 'REG_SZ'
USE_64 = constants.USE_REG_64
ARGS = [ROOT, PATH, NAME, VALUE, TYPE]


class RegistryTest(test_utils.GlazierTestCase):

  @mock.patch.object(registry.registry, 'set_value', autospec=True)
  def test_add_success(self, mock_set_value):
    registry.RegAdd(ARGS, None).Run()
    mock_set_value.assert_called_with(NAME, VALUE, ROOT, PATH, TYPE, USE_64)

  @mock.patch.object(registry.registry, 'set_value', autospec=True)
  def test_add_error(self, mock_set_value):
    mock_set_value.side_effect = registry.registry.RegistryWriteError(
        'some_name', 'some_value', 'some_path')
    ra = registry.RegAdd(ARGS, None)
    with self.assert_raises_with_validation(registry.ActionError):
      ra.Run()

  @mock.patch.object(registry.registry, 'set_value', autospec=True)
  def test_multi_add_success(self, mock_set_value):
    registry.RegAdd(ARGS, None).Run()
    mock_set_value.assert_called_with(NAME, VALUE, ROOT, PATH, TYPE, USE_64)

  # NOTE: Reverse decoration is intentional, due to @parameterized and @mock.
  @parameterized.named_parameters(
      ('_missing_args', [ROOT, PATH, NAME, VALUE]),
      ('_multiple_missing_args', [ARGS, [ROOT, PATH, NAME, VALUE]]),
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_multi_add_error(self, action_args, mock_buildinfo):
    ra = registry.RegAdd(action_args, mock_buildinfo)
    with self.assert_raises_with_validation(registry.ActionError):
      ra.Run()

  @mock.patch.object(registry.registry, 'remove_value', autospec=True)
  def test_del_success(self, mock_remove_value):
    registry.RegDel([ROOT, PATH, NAME], None).Run()
    mock_remove_value.assert_called_with(NAME, ROOT, PATH, USE_64)

  @mock.patch.object(registry.registry, 'remove_value', autospec=True)
  def test_del_error(self, mock_remove_value):
    mock_remove_value.side_effect = registry.registry.RegistryDeleteError(
        'some_name', 'some_path')
    rd = registry.RegDel([ROOT, PATH, NAME], None)
    with self.assert_raises_with_validation(registry.ActionError):
      rd.Run()

  @mock.patch.object(registry.registry, 'remove_value', autospec=True)
  def test_multi_del_success(self, mock_remove_value):
    registry.RegDel([ROOT, PATH, NAME, False], None).Run()
    mock_remove_value.assert_called_with(NAME, ROOT, PATH, False)

  @parameterized.named_parameters(
      ('_missing_arguments', [ROOT, PATH]),
      ('_multiple_missing_arguments', [[ROOT, PATH], [ROOT]]),
  )
  def test_multi_del_error(self, action_args):
    rd = registry.MultiRegDel(action_args, None)
    with self.assert_raises_with_validation(registry.ActionError):
      rd.Run()

  @parameterized.named_parameters(
      ('_list_not_passed', NAME),
      ('_too_many_args', [ROOT, PATH, NAME, NAME, TYPE, True, NAME]),
      ('_not_enough_args', [PATH, NAME, NAME, TYPE]),
      ('_type_error', [ROOT, PATH, NAME, '1', 'REG_DWORD']),
      ('_too_many_keys', [[ROOT, PATH, NAME, 1, TYPE],
                          [ROOT, PATH, NAME, 100, TYPE]]),
  )
  def test_add_validation_error(self, action_args):
    r = registry.RegAdd(action_args, None)
    with self.assert_raises_with_validation(registry.ValidationError):
      r.Validate()

  def test_add_validation_success(self):
    registry.RegAdd([ROOT, PATH, NAME, VALUE, TYPE], None).Validate()

  def test_multi_add_validation_success(self):
    registry.MultiRegAdd([ARGS, [ROOT, PATH, NAME, 100, 'REG_DWORD']],
                         None).Validate()

  @parameterized.named_parameters(
      ('_list_not_passed', NAME),
      ('_too_many_args', [ROOT, PATH, NAME, VALUE]),
      ('_not_enough_args', [PATH, NAME]),
      ('_too_many_keys', [[ROOT, PATH, NAME], [ROOT, PATH, NAME]]),
  )
  def test_del_validation_error(self, action_args):
    r = registry.RegDel(action_args, None)
    with self.assert_raises_with_validation(registry.ValidationError):
      r.Validate()

  def test_del_validation_success(self):
    registry.RegDel([ROOT, PATH, NAME], None).Validate()

  def test_multi_del_validation_success(self):
    registry.MultiRegDel([[ROOT, PATH, NAME], [ROOT, PATH, NAME]],
                         None).Validate()


if __name__ == '__main__':
  absltest.main()
