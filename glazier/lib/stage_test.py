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
"""Tests for glazier.lib.stage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from glazier.lib import stage
from gwinpy.registry import registry
import mock


class StageTest(absltest.TestCase):

  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_exit_stage(self, reg):
    stage.exit_stage(3)
    reg.assert_called_with('HKLM')
    reg.return_value.SetKeyValue.assert_has_calls([
        mock.call(
            key_path=stage.STAGES_ROOT + r'\3',
            key_name='End',
            key_value=mock.ANY,
            key_type='REG_SZ',
            use_64bit=True),
        mock.call(
            key_path=stage.STAGES_ROOT,
            key_name='_Active',
            key_value='',
            key_type='REG_SZ',
            use_64bit=True)
    ])

  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_exit_stage_invalid(self, reg):
    reg.return_value.SetKeyValue.side_effect = registry.RegistryError('Test')
    self.assertRaises(stage.Error, stage.exit_stage, 3)

  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_get_active_stage(self, reg):
    reg.return_value.GetKeyValue.return_value = '5'
    self.assertEqual(stage.get_active_stage(), '5')
    reg.assert_called_with('HKLM')
    reg.return_value.GetKeyValue.assert_called_with(
        key_path=stage.STAGES_ROOT, key_name='_Active', use_64bit=True)

  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_get_active_stage_none(self, reg):
    reg.return_value.GetKeyValue.side_effect = registry.RegistryError('Test')
    self.assertEqual(stage.get_active_stage(), None)

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_set_stage_first(self, reg, get_active):
    get_active.return_value = None
    stage.set_stage(1)
    reg.assert_called_with('HKLM')
    reg.return_value.SetKeyValue.assert_has_calls([
        mock.call(
            key_path=stage.STAGES_ROOT + r'\1',
            key_name='Start',
            key_value=mock.ANY,
            key_type='REG_SZ',
            use_64bit=True),
        mock.call(
            key_path=stage.STAGES_ROOT,
            key_name='_Active',
            key_value='1',
            key_type='REG_SZ',
            use_64bit=True)
    ])

  @mock.patch.object(stage, 'exit_stage', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_set_stage_next(self, unused_reg, get_active, exit_stage):
    get_active.return_value = '1'
    stage.set_stage(2)
    exit_stage.assert_called_with('1')

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'Registry', autospec=True)
  def test_set_stage_error(self, reg, get_active):
    get_active.return_value = None
    reg.return_value.SetKeyValue.side_effect = registry.RegistryError('Test')
    self.assertRaises(stage.Error, stage.set_stage, 3)

  def test_exit_stage_invalid_type(self):
    self.assertRaises(stage.Error, stage.set_stage, 'ABC')


if __name__ == '__main__':
  absltest.main()
