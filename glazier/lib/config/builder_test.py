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

from unittest import mock

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib import test_utils
from glazier.lib.config import builder
from glazier.lib.config import files

from glazier.lib import actions


class ConfigBuilderTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(ConfigBuilderTest, self).setUp()
    self.buildinfo = buildinfo.BuildInfo()
    self.cb = builder.ConfigBuilder(self.buildinfo)
    self.cb._task_list = []

  @mock.patch.object(buildinfo.BuildInfo, 'BuildPinMatch', autospec=True)
  def test_match_pin(self, mock_buildpinmatch):

    # All direct matching.
    mock_buildpinmatch.side_effect = iter([True, True])
    pins = {
        'computer_model': [
            'HP Z640 Workstation',
            'HP Z620 Workstation',
        ],
        'os_code': ['win7']
    }
    self.assertTrue(self.cb._MatchPin(pins))

    # Inverse match + direct match.
    mock_buildpinmatch.side_effect = iter([False, True])
    pins = {
        'computer_model': [
            'HP Z640 Workstation',
            '!HP Z620 Workstation',
        ],
        'os_code': ['win7']
    }
    self.assertFalse(self.cb._MatchPin(pins))

    # Inverse miss.
    mock_buildpinmatch.side_effect = iter([True, False])
    pins = {'computer_model': ['!VMWare Virtual Platform'], 'os_code': ['win8']}
    self.assertFalse(self.cb._MatchPin(pins))

    # Empty set.
    pins = {}
    self.assertTrue(self.cb._MatchPin(pins))

    # Inverse miss + direct mismatch.
    mock_buildpinmatch.side_effect = iter([False, False])
    pins = {'computer_model': ['VMWare Virtual Platform'], 'os_code': ['win8']}
    self.assertFalse(self.cb._MatchPin(pins))

    # Error
    mock_buildpinmatch.side_effect = buildinfo.IllegalPinError('some_pin')
    with self.assert_raises_with_validation(builder.SysInfoError):
      self.cb._MatchPin(pins)

  @mock.patch.object(builder.ConfigBuilder, '_ProcessAction', autospec=True)
  def test_realtime(self, mock_processaction):
    config = {'ShowChooser': ['Chooser Stuff']}
    self.cb._StoreControls(config, {})
    mock_processaction.assert_called_with(
        mock.ANY, 'ShowChooser', ['Chooser Stuff'])
    mock_processaction.reset_mock()
    config = {'CopyFile': [r'C:\input.txt', r'C:\output.txt']}
    self.cb._StoreControls(config, {})
    self.assertFalse(mock_processaction.called)
    self.assertEqual(self.cb._task_list[0]['data'], config)

  @mock.patch.object(builder.ConfigBuilder, '_Start', autospec=True)
  @mock.patch.object(files, 'Dump', autospec=True)
  def test_start_with_restart(self, mock_dump, mock_start):
    mock_start.side_effect = iter([actions.ServerChangeEvent('test'), None])
    self.cb.Start('/task/list/path.yaml', '/root1')
    mock_start.assert_has_calls([
        mock.call(self.cb, '/root1', 'build.yaml'),
        mock.call(self.cb, '', 'build.yaml'),
    ])
    mock_dump.assert_called_with('/task/list/path.yaml', [], mode='a')

  @mock.patch.object(builder.ConfigBuilder, '_StoreControls', autospec=True)
  @mock.patch.object(builder.download, 'PathCompile', autospec=True)
  @mock.patch.object(builder.files, 'Read', autospec=True)
  def test_start_with_server_change(
      self, mock_read, mock_pathcompile, mock_storecontrols):

    mock_pathcompile.return_value = '/'
    mock_read.return_value = {
        'controls': [{
            'ServerChangeEvent': ['https://glazier.example.com', '/']
        }]
    }
    mock_storecontrols.side_effect = iter([actions.ServerChangeEvent('test')])
    with self.assert_raises_with_validation(actions.ServerChangeEvent):
      self.cb._Start('/task/path/', 'list.yaml')
    self.assertEqual(self.cb._task_list[0]['data']['SetTimer'],
                     ['start_/task/path_list.yaml'])
    self.assertEqual(self.cb._task_list[1]['data']['SetTimer'],
                     ['stop_/task/path_list.yaml'])


if __name__ == '__main__':
  absltest.main()
