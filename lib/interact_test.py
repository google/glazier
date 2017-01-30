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
from glazier.lib import interact
import mock
from google.apputils import basetest


class InteractTest(basetest.TestCase):

  @mock.patch('__builtin__.raw_input', autospec=True)
  def testGetUsername(self, raw):
    raw.side_effect = iter(['invalid-name', '', '  ', 'username1'])
    self.assertEqual(interact.GetUsername(), 'username1')

  @mock.patch.object(interact.time, 'sleep', autospec=True)
  def testKeystroke(self, sleep):
    msvcrt = mock.Mock()
    msvcrt.kbhit.return_value = False
    sys.modules['msvcrt'] = msvcrt
    # no reply
    result = interact.Keystroke('mesg', timeout=1)
    self.assertEqual(result, None)
    self.assertEqual(sleep.call_count, 1)
    # reply
    msvcrt.kbhit.side_effect = iter([False, False, False, False, True])
    msvcrt.getch.return_value = 'v'
    result = interact.Keystroke('mesg', timeout=100)
    self.assertEqual(result, 'v')
    self.assertEqual(sleep.call_count, 6)
    # validation miss
    msvcrt.kbhit.side_effect = iter([True])
    result = interact.Keystroke('mesg', validator='[0-9]')
    self.assertEqual(result, None)

  @mock.patch('__builtin__.raw_input', autospec=True)
  def testPrompt(self, raw):
    raw.return_value = 'user*name'
    result = interact.Prompt('mesg', '^\\w+$')
    self.assertEqual(None, result)
    result = interact.Prompt('mesg')
    self.assertEqual('user*name', result)

if __name__ == '__main__':
  basetest.main()
