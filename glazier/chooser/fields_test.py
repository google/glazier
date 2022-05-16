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

from unittest import mock

from absl.testing import absltest
from glazier.chooser import fields


@mock.patch.object(fields, 'tk', autospec=True)
class FieldsTest(absltest.TestCase):

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, mock_tk):
    super(FieldsTest, self).setUp()
    self.root = mock_tk.Tk()

  def test_label(self, unused_tk):
    fields.Label(self.root, 'some label')

  def test_separator(self, unused_tk):
    fields.Separator(self.root)

  def test_toggle(self, unused_tk):
    opts = {'prompt': 'enable puppet',
            'options': [{'label': 'true', 'value': True, 'default': True},
                        {'label': 'false', 'value': False}]}
    toggle = fields.Toggle(self.root, opts)
    toggle.state.set.assert_called_with(True)
    toggle.Value()


class RadioMenuTest(absltest.TestCase):

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, mock_tk):
    super(RadioMenuTest, self).setUp()
    self.tk = mock_tk
    self.root = mock_tk.Tk()
    opts = {
        'prompt': 'choose locale',
        'options': [
            {'label': 'en-gb', 'value': 'en-gb', 'tip': ''},
            {'label': 'en-us', 'value': 'en-us', 'tip': '', 'default': True},
            {'label': 'es-es', 'value': 'es-es', 'tip': ''}
        ]}
    mock_tk.StringVar.return_value.get.return_value = 'en-us'
    self.rm = fields.RadioMenu(self.root, opts)

  def test_radio_menu(self):
    self.rm.select.set.assert_called_with('en-us')
    self.rm.button.configure.assert_called_with(text='en-us')


class TimerTest(absltest.TestCase):

  class Quit(Exception):
    pass

  @mock.patch.object(fields, 'tk', autospec=True)
  def setUp(self, mock_tk):
    super(TimerTest, self).setUp()
    self.root = mock_tk.Tk()
    self.root.quit.side_effect = TimerTest.Quit
    self.timer = fields.Timer(self.root, timeout=10)

  def test_pause(self):
    self.timer.Pause(None)
    self.assertEqual(self.timer._counter, -1)

  def test_countdown(self):
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
  absltest.main()
