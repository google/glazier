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

"""Tests for glazier.lib.interact."""

import sys
from unittest import mock

from absl.testing import absltest
from glazier.lib import interact


class InteractTest(absltest.TestCase):

  @mock.patch('builtins.input', autospec=True)
  def test_get_username(self, mock_input):
    mock_input.side_effect = iter(['invalid-name', '', '  ', 'username1'])
    self.assertEqual(interact.GetUsername(), 'username1')

  @mock.patch.object(interact, 'Prompt', autospec=True)
  def test_get_username_purpose(self, mock_prompt):
    mock_prompt.return_value = 'username1'
    self.assertEqual(interact.GetUsername('domain join'), 'username1')
    mock_prompt.assert_called_with(
        'Please enter your username for domain join: ',
        validator='^[a-zA-Z0-9]+$')

  @mock.patch.object(interact.time, 'sleep', autospec=True)
  def test_keystroke(self, mock_sleep):
    msvcrt = mock.Mock()
    msvcrt.kbhit.return_value = False
    sys.modules['msvcrt'] = msvcrt
    # no reply
    result = interact.Keystroke('mesg', timeout=1)
    self.assertIsNone(result)
    self.assertEqual(mock_sleep.call_count, 1)
    # special character reply
    msvcrt.kbhit.side_effect = iter([False, False, False, False, True])
    msvcrt.getch.return_value = b'0xe0'
    result = interact.Keystroke('mesg', timeout=100)
    self.assertEqual(result, '0xe0')
    self.assertEqual(mock_sleep.call_count, 6)
    # reply
    msvcrt.kbhit.side_effect = iter([False, False, False, False, True])
    msvcrt.getch.return_value = b'v'
    result = interact.Keystroke('mesg', timeout=100)
    self.assertEqual(result, 'v')
    self.assertEqual(mock_sleep.call_count, 11)
    # validation miss
    msvcrt.kbhit.side_effect = iter([True])
    result = interact.Keystroke('mesg', validator='[0-9]')
    self.assertIsNone(result)

  @mock.patch('builtins.input', autospec=True)
  def test_prompt(self, mock_input):
    mock_input.return_value = 'user*name'
    result = interact.Prompt('mesg', '^\\w+$')
    self.assertIsNone(result)
    result = interact.Prompt('mesg')
    self.assertEqual('user*name', result)

if __name__ == '__main__':
  absltest.main()
