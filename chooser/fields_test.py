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

"""Tests for glazier.chooser.fields."""

from glazier.chooser import fields
import mock
from google.apputils import basetest


@mock.patch.object(fields, 'tk', autospec=True)
class FieldsTest(basetest.TestCase):

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, tk):
    self.root = tk.Tk()

  def testLabel(self, unused_tk):
    fields.Label(self.root, 'some label')

  def testSeparator(self, unused_tk):
    fields.Separator(self.root)

  def testToggle(self, unused_tk):
    opts = {'prompt': 'enable puppet',
            'options': [{'label': 'true', 'value': True, 'default': True},
                        {'label': 'false', 'value': False}]}
    toggle = fields.Toggle(self.root, opts)
    toggle.state.set.assert_called_with(True)
    toggle.Value()


class RadioMenuTest(basetest.TestCase):

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, tk):
    self.tk = tk
    self.root = tk.Tk()
    opts = {
        'prompt': 'choose locale',
        'options': [
            {'label': 'en-gb', 'value': 'en-gb', 'tip': ''},
            {'label': 'en-us', 'value': 'en-us', 'tip': '', 'default': True},
            {'label': 'es-es', 'value': 'es-es', 'tip': ''}
        ]}
    tk.StringVar.return_value.get.return_value = 'en-us'
    self.rm = fields.RadioMenu(self.root, opts)

  def testRadioMenu(self):
    self.rm.select.set.assert_called_with('en-us')
    self.rm.button.configure.assert_called_with(text='en-us')


class TimerTest(basetest.TestCase):

  class Quit(Exception):
    pass

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, tk):
    self.root = tk.Tk()
    self.root.quit.side_effect = TimerTest.Quit
    self.timer = fields.Timer(self.root, timeout=10)

  def testPause(self):
    self.timer.Pause(None)
    self.assertEqual(self.timer._counter, -1)

  def testCountdown(self):
    # countdown
    self.assertEqual(self.timer._counter, 10)
    self.timer.Countdown()
    self.assertEqual(self.timer._counter, 9)
    self.assertTrue(self.root.after.called)
    self.assertFalse(self.root.quit.called)
    self.root.reset_mock()
    # timeout
    self.timer._counter = 0
    self.assertRaises(TimerTest.Quit, self.timer.Countdown)
    self.assertFalse(self.root.after.called)
    self.assertTrue(self.root.quit.called)
    self.root.reset_mock()
    # interrupt
    self.timer._counter = -1
    self.timer.Countdown()
    self.assertFalse(self.root.after.called)
    self.assertFalse(self.root.quit.called)


if __name__ == '__main__':
  basetest.main()
