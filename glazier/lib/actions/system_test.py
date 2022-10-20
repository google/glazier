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

"""Tests for glazier.lib.actions.system."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import events
from glazier.lib import test_utils
from glazier.lib.actions import system


class SystemTest(test_utils.GlazierTestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_pop(self, mock_buildinfo):
    r = system.Reboot([30, 'reboot for reasons', True], mock_buildinfo)
    with self.assert_raises_with_validation(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_reason(self, mock_buildinfo):
    r = system.Reboot([30, 'reboot for reasons'], mock_buildinfo)
    with self.assert_raises_with_validation(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '30')
    self.assertEqual(str(ex), 'reboot for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_reboot_timeout(self, mock_buildinfo):
    r = system.Reboot([10], mock_buildinfo)
    with self.assert_raises_with_validation(events.RestartEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '10')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  @parameterized.named_parameters(
      ('_invalid_arg_type_1', True),
      ('_invalid_arg_type_2', [30, 40]),
      ('_invalid_arg_type_3', [30, 'reasons', 'True']),
      ('_invalid_args_length', [1, 2, 3, 4]),
  )
  def test_reboot_validation_error(self, action_args):
    with self.assert_raises_with_validation(system.ValidationError):
      system.Reboot(action_args, None).Validate()

  @parameterized.named_parameters(
      ('_all_args', [30, 'reasons', True]),
      ('_no_pop_next', [30, 'reasons']),
      ('_no_reason', [30]),
  )
  def test_reboot_validation_success(self, action_args):
    system.Reboot(action_args, None).Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_pop(self, mock_buildinfo):
    r = system.Shutdown([15, 'shutdown for reasons', True], mock_buildinfo)
    with self.assert_raises_with_validation(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, True)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_reason(self, mock_buildinfo):
    r = system.Shutdown([15, 'shutdown for reasons'], mock_buildinfo)
    with self.assert_raises_with_validation(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '15')
    self.assertEqual(str(ex), 'shutdown for reasons')
    self.assertEqual(ex.pop_next, False)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_shutdown_timeout(self, mock_buildinfo):
    r = system.Shutdown([1], mock_buildinfo)
    with self.assert_raises_with_validation(events.ShutdownEvent) as evt:
      r.Run()
    ex = evt.exception
    self.assertEqual(ex.timeout, '1')
    self.assertEqual(str(ex), 'unspecified')
    self.assertEqual(ex.pop_next, False)

  @parameterized.named_parameters(
      ('_invalid_arg_type_1', True),
      ('_invalid_arg_type_2', [30, 40]),
      ('_invalid_arg_type_3', [30, 'reasons', 'True']),
      ('_invalid_args_length', [1, 2, 3, 4]),
  )
  def test_shutdown_validation_error(self, action_args):
    with self.assert_raises_with_validation(system.ValidationError):
      system.Shutdown(action_args, None).Validate()

  @parameterized.named_parameters(
      ('_all_args', [30, 'reasons', True]),
      ('_no_pop_next', [30, 'reasons']),
      ('_no_reason', [10]),
  )
  def test_shutdown_validation_success(self, action_args):
    system.Shutdown(action_args, None).Validate()

if __name__ == '__main__':
  absltest.main()
