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
"""Tests for glazier.lib.actions.timers."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import test_utils
from glazier.lib.actions import timers
from glazier.lib.actions.base import ValidationError

from glazier.lib import constants

KEY_PATH = r'{0}\{1}'.format(constants.REG_ROOT, 'Timers')
VALUE_NAME = 'build_yaml'
VALUE_DATA = '2019-11-11 13:33:37.133337'


class TimersTest(test_utils.GlazierTestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(timers.registry, 'set_value', autospec=True)
  @mock.patch.object(timers.logging, 'info', autospec=True)
  def test_set_timer(self, mock_info, mock_set_value, mock_buildinfo):
    mock_buildinfo.TimerGet.return_value = VALUE_DATA
    st = timers.SetTimer([VALUE_NAME], mock_buildinfo)
    st.Run()
    mock_buildinfo.TimerSet.assert_called_with(VALUE_NAME)
    mock_set_value.assert_called_with(
        'TIMER_' + VALUE_NAME, VALUE_DATA, 'HKLM', KEY_PATH, log=False)
    mock_info.assert_called_with('Set image timer: %s (%s)', VALUE_NAME,
                                 VALUE_DATA)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(timers.registry, 'set_value', autospec=True)
  def test_set_timer_error(self, mock_set_value, mock_buildinfo):
    mock_buildinfo.TimerGet.return_value = VALUE_DATA
    mock_set_value.side_effect = timers.registry.RegistryWriteError(
        'some_name', 'some_value')
    st = timers.SetTimer([VALUE_NAME], mock_buildinfo)
    with self.assert_raises_with_validation(timers.ActionError):
      st.Run()

  @parameterized.named_parameters(
      ('_invalid_arg_type_1', VALUE_NAME),
      ('_invalid_args_length', [1, 2, 3]),
      ('_invalid_arg_type_2', [1]),
  )
  def test_set_timer_validation_error(self, action_args):
    with self.assert_raises_with_validation(ValidationError):
      timers.SetTimer(action_args, None).Validate()

  def test_set_timer_validation_success(self):
    timers.SetTimer([VALUE_NAME], None).Validate()


if __name__ == '__main__':
  absltest.main()
