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

from absl.testing import absltest
from glazier.lib.actions import registry
from glazier.lib.actions import timers
from glazier.lib.actions.base import ValidationError
import mock


class TimersTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(registry.registry, 'Registry', autospec=True)
  def testSetTimer(self, winreg, build_info):
    args = ['Timer1']
    build_info.TimerGet.return_value = '2019-11-11 13:33:37.133337'
    st = timers.SetTimer(args, build_info)
    st.Run()
    build_info.TimerSet.assert_called_with('Timer1')
    key_name = r'%s\%s' % (timers.constants.REG_ROOT, 'Timers')

    # Successfully add registry keys
    args = [
        'HKLM', key_name, 'TIMER_image_start',
        '2019-11-11 13:33:37.133337',
        'REG_SZ', False
    ]
    ra = timers.RegAdd(args, build_info)
    ra.Run()

    # Fail to add registry key
    skv = winreg.return_value.SetKeyValue
    skv.side_effect = registry.registry.RegistryError
    self.assertRaises(registry.ActionError, ra.Run)

  def testSetTimerValidate(self):
    st = timers.SetTimer('Timer1', None)
    self.assertRaises(ValidationError, st.Validate)
    st = timers.SetTimer([1, 2, 3], None)
    self.assertRaises(ValidationError, st.Validate)
    st = timers.SetTimer([1], None)
    self.assertRaises(ValidationError, st.Validate)
    st = timers.SetTimer(['Timer1'], None)
    st.Validate()


if __name__ == '__main__':
  absltest.main()
