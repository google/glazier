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

"""Tests for glazier.lib.config.runner."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import events
from glazier.lib import test_utils
from glazier.lib.config import base
from glazier.lib.config import files
from glazier.lib.config import runner


class ConfigRunnerTest(test_utils.GlazierTestCase):

  def setUp(self):

    super(ConfigRunnerTest, self).setUp()
    self.buildinfo = buildinfo.BuildInfo()
    constants.FLAGS.verify_urls = None

    self.cr = runner.ConfigRunner(self.buildinfo)
    self.task_list_path = self.create_tempfile(
        file_path='task_list.yaml').full_path
    self.cr._task_list_path = self.task_list_path

  @mock.patch.object(runner.files, 'Remove', autospec=True)
  @mock.patch.object(base.actions, 'pull', autospec=True)
  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def test_iteration(self, mock_dump, mock_pull, mock_remove):
    conf = [{
        'data': {
            'pull': 'val1'
        },
        'path': ['/path1']
    }, {
        'data': {
            'pull': 'val2'
        },
        'path': ['/path2']
    }, {
        'data': {
            'pull': 'val3'
        },
        'path': ['/path3']
    }]
    self.cr._ProcessTasks(conf)
    mock_dump.assert_has_calls([
        mock.call(self.cr._task_list_path, conf[1:], mode='w'),
        mock.call(self.cr._task_list_path, conf[2:], mode='w'),
        mock.call(self.cr._task_list_path, [], mode='w')
    ])
    mock_pull.assert_has_calls([])
    self.assertTrue(mock_remove.called)

  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def test_pop_task(self, mock_dump):
    self.cr._PopTask([1, 2, 3])
    mock_dump.assert_called_with(self.task_list_path, [2, 3], mode='w')
    mock_dump.side_effect = runner.files.FileRemoveError('/some/file/path')
    with self.assert_raises_with_validation(runner.ConfigRunnerError):
      self.cr._PopTask([1, 2])

  @mock.patch.object(runner.files, 'Remove', autospec=True)
  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def test_pop_last_task(self, mock_dump, mock_remove):
    self.cr._PopTask([1])
    mock_dump.assert_called_with(self.task_list_path, [], mode='w')
    mock_remove.assert_called_with(self.task_list_path)

  @mock.patch.object(runner.power, 'Restart', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_ProcessAction', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_PopTask', autospec=True)
  def test_restart_events(self, mock_poptask, mock_processaction, mock_restart):
    conf = [{
        'data': {
            'Shutdown': ['25', 'Reason']
        },
        'path': ['path1']
    }]
    event = events.RestartEvent('Some reason', timeout=25)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_restart.assert_called_with(25, 'Some reason')
    self.assertTrue(mock_poptask.called)
    mock_poptask.reset_mock()

    # with retry
    event = events.RestartEvent(
        'Some other reason', timeout=10, retry_on_restart=True)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_restart.assert_called_with(10, 'Some other reason')
    self.assertFalse(mock_poptask.called)

    # with pop
    event = events.RestartEvent(
        'Some other reason', timeout=10, pop_next=True)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_restart.assert_called_with(10, 'Some other reason')
    self.assertTrue(mock_poptask.called)

  @mock.patch.object(runner.power, 'Shutdown', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_ProcessAction', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_PopTask', autospec=True)
  def test_shutdown_events(
      self, mock_poptask, mock_processaction, mock_shutdown):

    conf = [{
        'data': {
            'Restart': ['25', 'Reason']
        },
        'path': ['path1']
    }]
    event = events.ShutdownEvent('Some reason', timeout=25)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_shutdown.assert_called_with(25, 'Some reason')
    self.assertTrue(mock_poptask.called)
    mock_poptask.reset_mock()

    # with retry
    event = events.ShutdownEvent(
        'Some other reason', timeout=10, retry_on_restart=True)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_shutdown.assert_called_with(10, 'Some other reason')
    self.assertFalse(mock_poptask.called)

    # with pop
    event = events.ShutdownEvent(
        'Some other reason', timeout=10, pop_next=True)
    mock_processaction.side_effect = event
    with self.assert_raises_with_validation(SystemExit):
      self.cr._ProcessTasks(conf)
    mock_shutdown.assert_called_with(10, 'Some other reason')
    self.assertTrue(mock_poptask.called)

  @mock.patch.object(base.actions, 'SetTimer', autospec=True)
  def test_process_with_action_error(self, mock_settimer):
    mock_settimer.side_effect = base.actions.ActionError
    with self.assert_raises_with_validation(runner.ConfigRunnerError):
      self.cr._ProcessTasks(
          [{
              'data': {
                  'SetTimer': ['Timer1']
              },
              'path': ['/autobuild']
          }]
      )

  def test_process_with_invalid_command(self):
    with self.assert_raises_with_validation(runner.ConfigRunnerError):
      self.cr._ProcessTasks(
          [{
              'data': {
                  'BadSetTimer': ['Timer1']
              },
              'path': ['/autobuild']
          }]
      )

  @mock.patch.object(runner.files, 'Read', autospec=True)
  def test_start_with_missing_file(self, mock_read):
    mock_read.side_effect = files.FileDownloadError('some_path')
    with self.assert_raises_with_validation(runner.ConfigRunnerError):
      self.cr.Start('/tmp/path/missing.yaml')

  @mock.patch.object(base.actions, 'SetTimer', autospec=True)
  @mock.patch.object(runner.files, 'Read', autospec=True)
  @mock.patch.object(runner.files, 'Remove', autospec=True)
  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def test_start_with_actions(
      self, mock_dump, mock_remove, mock_read, mock_settimer):

    mock_read.return_value = [{
        'data': {
            'SetTimer': ['TestTimer']
        },
        'path': ['/autobuild']
    }]
    self.cr.Start('/tmp/path/tasks.yaml')
    mock_read.assert_called_with('/tmp/path/tasks.yaml')
    mock_settimer.assert_called_with(
        build_info=self.buildinfo, args=['TestTimer'])
    self.assertTrue(mock_settimer.return_value.Run.called)
    self.assertTrue(mock_dump.called)
    self.assertTrue(mock_remove.called)

  @mock.patch.object(runner.download.Download, 'CheckUrl', autospec=True)
  def test_verify_urls(self, mock_checkurl):
    mock_checkurl.return_value = True
    constants.FLAGS.verify_urls = ['http://www.example.com/']
    self.cr._ProcessTasks([])
    mock_checkurl.assert_called_with(mock.ANY, 'http://www.example.com/', [200])
    # fail
    mock_checkurl.return_value = False
    with self.assert_raises_with_validation(runner.CheckUrlError):
      self.cr._ProcessTasks([])


if __name__ == '__main__':
  absltest.main()
