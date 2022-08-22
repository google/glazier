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

import datetime
from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import flagsaver
from glazier.lib import stage
from glazier.lib import test_utils

FLAGS = flags.FLAGS


class StageTest(test_utils.GlazierTestCase):

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_exit_stage(self, mock_set_value):
    stage.exit_stage(3)
    mock_set_value.assert_has_calls([
        mock.call('End', mock.ANY, 'HKLM', stage.STAGES_ROOT + r'\3'),
        mock.call('_Active', '', 'HKLM', stage.STAGES_ROOT)
    ])

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_exit_stage_invalid(self, mock_set_value):
    mock_set_value.side_effect = stage.registry.RegistryWriteError(
        'some_name', 'some_value', 'some_path')
    with self.assert_raises_with_validation(stage.ExitError):
      stage.exit_stage(3)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  def test_get_active_stage(self, mock_check_expiration, mock_get_value):
    mock_get_value.return_value = '5'
    self.assertEqual(stage.get_active_stage(), 5)
    mock_get_value.assert_called_with('_Active', 'HKLM', stage.STAGES_ROOT)
    mock_check_expiration.assert_called_with(5)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_with_end(self, mock_load_time, mock_get_value):
    mock_get_value.return_value = None
    mock_load_time.side_effect = (datetime.datetime(2019, 11, 6, 17, 38, 52, 0),
                                  datetime.datetime(2019, 11, 6, 19, 18, 52, 0))
    self.assertEqual(
        stage.get_active_time(3), datetime.timedelta(hours=1, minutes=40))
    mock_load_time.assert_has_calls(
        [mock.call(3, 'Start'), mock.call(3, 'End')])

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_no_start(self, mock_load_time, mock_get_value):
    mock_get_value.return_value = None
    mock_load_time.side_effect = (None,
                                  datetime.datetime(2019, 11, 6, 19, 18, 52, 0))
    with self.assert_raises_with_validation(stage.InvalidStartTimeError):
      stage.get_active_time(4)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_utc_now', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_no_end(self, mock_load_time, mock_utc_now,
                                  mock_get_value):

    start = datetime.datetime(2019, 10, 20, 19, 18, 12, 0)
    now = datetime.datetime(2019, 11, 6, 10, 45, 12, 0)
    mock_utc_now.return_value = now
    mock_get_value.return_value = None
    mock_load_time.side_effect = (start, None)
    self.assertEqual(
        stage.get_active_time(6),
        datetime.timedelta(days=16, hours=15, minutes=27))

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_complete(self, mock_get_active_stage, mock_get_start_end):
    mock_get_active_stage.return_value = 5
    mock_get_start_end.return_value = (datetime.datetime.now(),
                                       datetime.datetime.now())
    self.assertEqual(stage.get_status(), 'Complete')

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_expired(self, mock_get_active_stage,
                              mock_check_expiration, mock_get_start_end):

    mock_get_active_stage.return_value = 5
    mock_get_start_end.return_value = (datetime.datetime.now(), None)
    mock_check_expiration.side_effect = stage.ExpirationError('stage_id')
    self.assertEqual(stage.get_status(), 'Expired')
    self.assertTrue(mock_check_expiration.called)

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_no_start(self, mock_get_active_stage, mock_get_start_end):
    mock_get_active_stage.return_value = 4
    mock_get_start_end.return_value = (None, None)
    self.assertEqual(stage.get_status(), 'Unknown')

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_running(self, mock_get_active_stage,
                              mock_check_expiration, mock_get_start_end):

    mock_get_active_stage.return_value = 5
    mock_get_start_end.return_value = (datetime.datetime.now(), None)
    self.assertEqual(stage.get_status(), 'Running')
    self.assertTrue(mock_check_expiration.called)

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_unknown(self, mock_get_active_stage):
    mock_get_active_stage.return_value = None
    self.assertEqual(stage.get_status(), 'Unknown')

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_load_time_parse(self, mock_get_value):
    mock_get_value.return_value = '2019-11-06T17:37:43.279253'
    self.assertEqual(
        stage._load_time(1, 'Start'),
        datetime.datetime(2019, 11, 6, 17, 37, 43, 279253))

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_load_time_parse_err(self, mock_get_value):
    mock_get_value.return_value = '12345'
    self.assertIsNone(stage._load_time(1, 'End'))

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_set_stage_first(self, mock_get_value, mock_set_value):
    mock_get_value.return_value = None
    stage.set_stage(1)
    mock_set_value.assert_has_calls([
        mock.call('Start', mock.ANY, 'HKLM', stage.STAGES_ROOT + r'\1'),
        mock.call('_Active', '1', 'HKLM', stage.STAGES_ROOT)
    ])

  @mock.patch.object(stage, 'exit_stage', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_set_stage_next(self, mock_set_value, get_active, mock_exit_stage):
    get_active.return_value = 1
    stage.set_stage(2)
    mock_exit_stage.assert_called_with(1)
    mock_set_value.assert_called_with('_Active', '2', 'HKLM', stage.STAGES_ROOT)

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_set_stage_error(self, mock_set_value, mock_get_active_stage):
    mock_get_active_stage.return_value = None
    mock_set_value.side_effect = stage.registry.RegistryWriteError(
        'some_name', 'some_value', 'some_path')
    with self.assert_raises_with_validation(stage.UpdateError):
      stage.set_stage(3)

  def test_exit_stage_invalid_type(self):
    with self.assert_raises_with_validation(stage.InvalidStageIdError):
      stage.set_stage('ABC')

  @flagsaver.flagsaver
  @mock.patch.object(stage, 'get_active_time', autospec=True)
  def test_stage_expiration(self, mock_get_active_stage):
    end = stage._utc_now()
    start = end - datetime.timedelta(minutes=90)
    mock_get_active_stage.return_value = (end - start)
    FLAGS.stage_timeout_minutes = 120
    stage._check_expiration(3)
    FLAGS.stage_timeout_minutes = 60
    with self.assert_raises_with_validation(stage.ExpirationError):
      stage._check_expiration(3)
    mock_get_active_stage.assert_called_with(stage_id=3)


if __name__ == '__main__':
  absltest.main()
