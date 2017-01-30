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
from glazier.lib import timers
import mock
from google.apputils import basetest


class TimersTest(basetest.TestCase):

  def setUp(self):
    self.t = timers.Timers()

  @mock.patch.object(timers.datetime, 'datetime', autospec=True)
  def testNow(self, dt):
    now = datetime.datetime.utcnow()
    dt.utcnow.return_value = now
    self.assertEqual(self.t.Now(), now)

  def testGetAll(self):
    time_2 = datetime.datetime.now()
    self.t.Set('timer_1')
    self.t.Set('timer_2', at_time=time_2)
    self.assertEqual(self.t.Get('timer_2'), time_2)
    all_t = self.t.GetAll()
    self.assertIn('timer_1', all_t)
    self.assertIn('timer_2', all_t)

if __name__ == '__main__':
  basetest.main()
