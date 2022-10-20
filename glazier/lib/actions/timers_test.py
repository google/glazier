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

import datetime
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import buildinfo
from glazier.lib import test_utils
from glazier.lib import timers
from glazier.lib.actions import timers as timers_action
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import ValidationError

from glazier.lib import constants

_KEY_PATH = fr'{constants.REG_ROOT}\Timers'
_VALUE_NAME = 'build_yaml'
_VALUE_DATA = str(datetime.datetime.now(tz=datetime.timezone.utc))


class TimersTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(TimersTest, self).setUp()
    self.timers = timers.Timers()
    self._build_info = buildinfo.BuildInfo()

  @mock.patch.object(timers.Timers, 'Set', autospec=True)
  @mock.patch.object(timers.Timers, 'Get', autospec=True)
  def test_set_timer(self, mock_timers_get, mock_timers_set):
    mock_timers_get.return_value = _VALUE_DATA
    st = timers_action.SetTimer([_VALUE_NAME], self._build_info)
    st.Run()
    mock_timers_set.assert_called_with(mock.ANY, _VALUE_NAME)

  @mock.patch.object(timers.Timers, 'Set', autospec=True)
  @mock.patch.object(timers.Timers, 'Get', autospec=True)
  def test_set_timer_error(self, mock_timers_get, mock_timers_set):
    mock_timers_get.return_value = _VALUE_DATA
    mock_timers_set.side_effect = timers.SetTimerError('name', 'value')
    st = timers_action.SetTimer([_VALUE_NAME], self._build_info)
    with self.assert_raises_with_validation(ActionError):
      st.Run()

  @parameterized.named_parameters(
      ('_invalid_arg_type_1', _VALUE_NAME),
      ('_invalid_args_length', [1, 2, 3]),
      ('_invalid_arg_type_2', [1]),
  )
  def test_set_timer_validation_error(self, action_args):
    with self.assert_raises_with_validation(ValidationError):
      timers_action.SetTimer(action_args, None).Validate()

  def test_set_timer_validation_success(self):
    timers_action.SetTimer([_VALUE_NAME], None).Validate()


if __name__ == '__main__':
  absltest.main()
