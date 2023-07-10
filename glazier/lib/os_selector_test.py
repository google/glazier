# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Tests for OS Selector library."""

import builtins
from unittest import mock

from absl.testing import absltest
from glazier.lib import os_selector
from glazier.lib import test_utils
import yaml

_SELECTOR_YAML = """
os:
  - ['Windows 10',['windows-10-stable','windows-10-testing','windows-10-unstable'],['20FR', 'HP Z240 SFF Workstation','Surface Pro 3'],False]
  - ['Windows
    7',['windows-win-7-stable-x64','windows-win-7-testing-x64','windows-win-7-unstable-x64', 'windows-7-special'],['!PowerEdge'],False]
  - ['Windows 2012R2 Standard Edition',['win2012r2-core-x64-se','win2012r2-core-testing-x64-se','win2012r2-core-unstable-x64-se'],['PowerEdge', 'DSS', 'VMware'],False]
  - ['Windows 7 deprecated',['windows-gwin-7-stable-x64','windows-gwin-7-testing-x64','windows-gwin-7-unstable-x64', 'windows-7-special'],['Surface Pro 3'],True]
"""


class OsSelectorTest(test_utils.GlazierTestCase):

  @mock.patch.object(os_selector.files, 'Read', autospec=True)
  def setUp(self, mock_read):
    super().setUp()
    mock_read.returns = _SELECTOR_YAML
    self.selector = os_selector.OSSelector()
    self.selector.config = yaml.safe_load(_SELECTOR_YAML)

  def test_strip_margin(self):
    expected = '\n'.join((
        '',
        'line 1',
        '    line 2',
        '| line 3',))
    test1 = """
    |line 1
    |    line 2
    || line 3"""
    test2 = """
    #line 1
    line 2
    #| line 3"""
    self.assertEqual(os_selector._StripMargin(test1), expected)
    self.assertEqual(os_selector._StripMargin(test2, '#'), expected)

  def test_show_menu(self):
    self.selector.model = 'Surface Pro 3'
    self.selector._TrimOSConfig()
    self.assertRegex(self.selector._ShowMenu(), 'p')
    self.assertRegex(self.selector._ShowMenu(), '1')
    self.assertRegex(self.selector._ShowMenu(), '2')
    self.assertRegex(self.selector._ShowMenu(), '3')
    self.selector.model = 'Surface Pro 1'
    self.selector.config = yaml.safe_load(_SELECTOR_YAML)
    self.selector._TrimOSConfig()
    self.assertRegex(self.selector._ShowMenu(), '1')
    self.assertNotRegex(self.selector._ShowMenu(), '2')

  def test_print_os_option(self):
    self.selector.model = 'Surface Pro 3'
    selector_file = yaml.safe_load(_SELECTOR_YAML)
    self.selector._TrimOSConfig()
    self.assertEqual(
        self.selector._PrintOSOption(selector_file['os'][0], 0),
        '1. Windows 10')
    self.assertEqual(self.selector._PrintOSOption(selector_file['os'][3],
                                                  0), '')

  def test_os_code_no_flag(self):
    os_code = self.selector.config['os'][0][1][0]
    self.assertEqual(os_code, self.selector._OSCode())

  def test_os_code_no_flag_index_error(self):
    self.selector.config['os'] = []
    with self.assertRaises(os_selector.UnsupportedModelError):
      self.selector._OSCode()

  @mock.patch.object(os_selector.interact, 'Keystroke', autospec=True)
  @mock.patch.object(builtins, 'input', autospec=True)
  def test_auto_or_manual(self, mock_input, mock_keystroke
                          ):
    mock_keystroke.return_value = 'a'
    mock_input.return_value = '2'
    mock_input.return_value = '1'
    self.selector.AutoOrManual('model')
    self.assertEqual(self.selector.AutoOrManual('model'),
                     'windows-win-7-stable-x64')

  @mock.patch.object(builtins, 'input', autospec=True)
  def test_get_response_client(self, mock_input):
    mock_input.return_value = 1
    mock_input.return_value = '1'
    self.selector.model = '20FR'
    self.assertTrue(self.selector._GetResponse(), 'windows-10-stable')

if __name__ == '__main__':
  absltest.main()
