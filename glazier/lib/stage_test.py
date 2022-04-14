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


FLAGS = flags.FLAGS


class StageTest(absltest.TestCase):

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_exit_stage(self, sv):
    stage.exit_stage(3)
    sv.assert_has_calls([
        mock.call('End', mock.ANY, 'HKLM', stage.STAGES_ROOT + r'\3'),
        mock.call('_Active', '', 'HKLM', stage.STAGES_ROOT)
    ])

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_exit_stage_invalid(self, sv):
    sv.side_effect = stage.registry.Error
    self.assertRaises(stage.Error, stage.exit_stage, 3)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  def test_get_active_stage(self, check, gv):
    gv.return_value = '5'
    self.assertEqual(stage.get_active_stage(), 5)
    gv.assert_called_with('_Active', 'HKLM', stage.STAGES_ROOT)
    check.assert_called_with(5)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_get_active_stage_none(self, gv):
    gv.side_effect = stage.registry.Error
    self.assertIsNone(stage.get_active_stage())

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_with_end(self, load, gv):
    gv.return_value = None
    load.side_effect = (datetime.datetime(2019, 11, 6, 17, 38, 52, 0),
                        datetime.datetime(2019, 11, 6, 19, 18, 52, 0))
    self.assertEqual(
        stage.get_active_time(3), datetime.timedelta(hours=1, minutes=40))
    load.assert_has_calls([
        mock.call(3, 'Start'),
        mock.call(3, 'End')
    ])

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_no_start(self, load, gv):
    gv.return_value = None
    load.side_effect = (None, datetime.datetime(2019, 11, 6, 19, 18, 52, 0))
    self.assertRaises(stage.Error, stage.get_active_time, 4)

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  @mock.patch.object(stage, '_utc_now', autospec=True)
  @mock.patch.object(stage, '_load_time', autospec=True)
  def test_get_active_time_no_end(self, load, utc, gv):
    start = datetime.datetime(2019, 10, 20, 19, 18, 12, 0)
    now = datetime.datetime(2019, 11, 6, 10, 45, 12, 0)
    utc.return_value = now
    gv.return_value = None
    load.side_effect = (start, None)
    self.assertEqual(
        stage.get_active_time(6),
        datetime.timedelta(days=16, hours=15, minutes=27))

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_complete(self, active, start_end):
    active.return_value = 5
    start_end.return_value = (datetime.datetime.now(), datetime.datetime.now())
    self.assertEqual(stage.get_status(), 'Complete')

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_expired(self, active, expiration, start_end):
    active.return_value = 5
    start_end.return_value = (datetime.datetime.now(), None)
    expiration.side_effect = stage.Error('Expired')
    self.assertEqual(stage.get_status(), 'Expired')
    self.assertTrue(expiration.called)

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_no_start(self, active, start_end):
    active.return_value = 4
    start_end.return_value = (None, None)
    self.assertEqual(stage.get_status(), 'Unknown')

  @mock.patch.object(stage, '_get_start_end', autospec=True)
  @mock.patch.object(stage, '_check_expiration', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_running(self, active, expiration, start_end):
    active.return_value = 5
    start_end.return_value = (datetime.datetime.now(), None)
    self.assertEqual(stage.get_status(), 'Running')
    self.assertTrue(expiration.called)

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  def test_get_status_unknown(self, active):
    active.return_value = None
    self.assertEqual(stage.get_status(), 'Unknown')

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_load_time_parse(self, gv):
    gv.return_value = '2019-11-06T17:37:43.279253'
    self.assertEqual(
        stage._load_time(1, 'Start'),
        datetime.datetime(2019, 11, 6, 17, 37, 43, 279253))

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_load_time_parse_err(self, gv):
    gv.return_value = '12345'
    self.assertIsNone(stage._load_time(1, 'End'))

  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_load_time_reg_err(self, gv):
    gv.side_effect = stage.registry.Error
    self.assertIsNone(stage._load_time(1, 'End'))

  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  @mock.patch.object(stage.registry, 'get_value', autospec=True)
  def test_set_stage_first(self, gv, sv):
    gv.return_value = None
    stage.set_stage(1)
    sv.assert_has_calls([
        mock.call('Start', mock.ANY, 'HKLM', stage.STAGES_ROOT + r'\1'),
        mock.call('_Active', '1', 'HKLM', stage.STAGES_ROOT)
    ])

  @mock.patch.object(stage, 'exit_stage', autospec=True)
  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_set_stage_next(self, reg, get_active, exit_stage):
    get_active.return_value = 1
    stage.set_stage(2)
    exit_stage.assert_called_with(1)
    reg.assert_called_with('_Active', '2', 'HKLM', stage.STAGES_ROOT)

  @mock.patch.object(stage, 'get_active_stage', autospec=True)
  @mock.patch.object(stage.registry, 'set_value', autospec=True)
  def test_set_stage_error(self, sv, get_active):
    get_active.return_value = None
    sv.side_effect = stage.registry.Error
    self.assertRaises(stage.Error, stage.set_stage, 3)

  def test_exit_stage_invalid_type(self):
    self.assertRaises(stage.Error, stage.set_stage, 'ABC')

  @flagsaver.flagsaver
  @mock.patch.object(stage, 'get_active_time', autospec=True)
  def test_stage_expiration(self, get_active):
    end = stage._utc_now()
    start = end - datetime.timedelta(minutes=90)
    get_active.return_value = (end - start)
    FLAGS.stage_timeout_minutes = 120
    stage._check_expiration(3)
    FLAGS.stage_timeout_minutes = 60
    self.assertRaises(stage.Error, stage._check_expiration, 3)
    get_active.assert_called_with(stage_id=3)


if __name__ == '__main__':
  absltest.main()
