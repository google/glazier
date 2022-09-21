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

"""Tests for glazier.lib.timers."""

import datetime
from unittest import mock

from absl.testing import absltest
from glazier.lib import registry
from glazier.lib import timers

_FAKE_TIMER = str(
    datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=6))))
_FAKE_DICT = {
    'TIMER_fake_1':
        _FAKE_TIMER,
    'TIMER_fake_2':
        str(
            datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=18)))),
    'TIMER_fake_3':
        str(
            datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=23)))),
}


class TimersTest(absltest.TestCase):

  @mock.patch.object(registry, 'get_value', autospec=True)
  def test_get(self, mock_get_value):
    mock_get_value.return_value = _FAKE_TIMER
    self.assertEqual(
        timers.Timers().Get('TIMER_fake_1'),
        datetime.datetime.strptime(_FAKE_TIMER, '%Y-%m-%d %H:%M:%S.%f%z'))

  @mock.patch.object(registry, 'get_keys_and_values', autospec=True)
  def test_get_all(self, mock_get_keys_and_values):
    mock_get_keys_and_values.return_value = _FAKE_DICT

    timers_dict = {}
    for k, v in _FAKE_DICT.items():
      timers_dict[k] = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f%z')
    self.assertEqual(timers.Timers().GetAll(), timers_dict)

  @mock.patch.object(registry, 'set_value', autospec=True)
  def test_set(self, mock_set_value):
    timers.Timers().Set('fake_1')
    mock_set_value.assert_called_with(
        'TIMER_fake_1', mock.ANY, 'HKLM', timers.TIMERS_PATH, log=False)
    mock_set_value.side_effect = registry.Error
    with self.assertRaises(timers.SetTimerError):
      timers.Timers().Set('fake_2')

if __name__ == '__main__':
  absltest.main()
