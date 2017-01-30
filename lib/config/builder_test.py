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

"""Tests for glazier.lib.config.builder."""

from pyfakefs import fake_filesystem
from glazier.lib import buildinfo
from glazier.lib.config import builder
import mock
from google.apputils import basetest


class ConfigBuilderTest(basetest.TestCase):

  def setUp(self):

    self.buildinfo = buildinfo.BuildInfo()
    # filesystem
    self.filesystem = fake_filesystem.FakeFilesystem()
    self.cb = builder.ConfigBuilder(self.buildinfo)
    self.cb._task_list = []

  @mock.patch.object(buildinfo.BuildInfo, 'BuildPinMatch', autospec=True)
  def testMatchPin(self, bpm):
    # All direct matching.
    bpm.side_effect = iter([True, True])
    pins = {
        'computer_model': [
            'HP Z640 Workstation',
            'HP Z620 Workstation',
        ],
        'os_code': ['win7']
    }
    self.assertTrue(self.cb._MatchPin(pins))
    # Inverse match + direct match.
    bpm.side_effect = iter([False, True])
    pins = {
        'computer_model': [
            'HP Z640 Workstation',
            '!HP Z620 Workstation',
        ],
        'os_code': ['win7']
    }
    self.assertFalse(self.cb._MatchPin(pins))
    # Inverse miss.
    bpm.side_effect = iter([True, False])
    pins = {
        'computer_model': ['!VMWare Virtual Platform'],
        'os_code': ['win8']
    }
    self.assertFalse(self.cb._MatchPin(pins))
    # Empty set.
    pins = {}
    self.assertTrue(self.cb._MatchPin(pins))
    # Inverse miss + direct mismatch.
    bpm.side_effect = iter([False, False])
    pins = {
        'computer_model': ['VMWare Virtual Platform'],
        'os_code': ['win8']
    }
    self.assertFalse(self.cb._MatchPin(pins))
    # Error
    bpm.side_effect = buildinfo.BuildInfoError
    self.assertRaises(builder.ConfigBuilderError, self.cb._MatchPin, pins)

  @mock.patch.object(builder.ConfigBuilder, '_ProcessAction', autospec=True)
  def testRealtime(self, process):
    config = {'ShowChooser': ['Chooser Stuff']}
    self.cb._StoreControls(config, {})
    process.assert_called_with(mock.ANY, 'ShowChooser', ['Chooser Stuff'])
    process.reset_mock()
    config = {'CopyFile': [r'C:\input.txt', r'C:\output.txt']}
    self.cb._StoreControls(config, {})
    self.assertFalse(process.called)
    self.assertEqual(self.cb._task_list[0]['data'], config)


if __name__ == '__main__':
  basetest.main()
