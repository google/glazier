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

from pyfakefs import fake_filesystem
from pyfakefs import fake_filesystem_shutil
from glazier.lib import buildinfo
from glazier.lib.config import runner
import mock
from google.apputils import basetest


class ConfigRunnerTest(basetest.TestCase):

  def setUp(self):
    self.buildinfo = buildinfo.BuildInfo()
    # filesystem
    self.filesystem = fake_filesystem.FakeFilesystem()
    runner.os = fake_filesystem.FakeOsModule(self.filesystem)
    runner.open = fake_filesystem.FakeFileOpen(self.filesystem)
    runner.shutil = fake_filesystem_shutil.FakeShutilModule(self.filesystem)
    self.cr = runner.ConfigRunner(self.buildinfo)
    self.cr._task_list_path = '/tmp/task_list.yaml'

  @mock.patch.object(runner.base.actions, 'pull', autospec=True)
  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def testIteration(self, dump, unused_get):
    conf = [{'data': {'pull': 'val1'},
             'path': ['path1']}, {'data': {'pull': 'val2'},
                                  'path': ['path2']}, {'data': {'pull': 'val3'},
                                                       'path': ['path3']}]
    self.cr._ProcessTasks(conf)
    dump.assert_has_calls([
        mock.call(
            self.cr._task_list_path, conf[1:], mode='w'), mock.call(
                self.cr._task_list_path, conf[2:], mode='w'), mock.call(
                    self.cr._task_list_path, [], mode='w')
    ])

  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def testPopTask(self, dump):
    self.cr._PopTask([1, 2, 3])
    dump.assert_called_with('/tmp/task_list.yaml', [2, 3], mode='w')
    dump.side_effect = runner.files.Error
    with self.assertRaises(runner.ConfigRunnerError):
      self.cr._PopTask([1, 2])

  @mock.patch.object(runner.power, 'Restart', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_ProcessAction', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_PopTask', autospec=True)
  def testRestartEvents(self, pop, action, restart):
    conf = [{'data': {'Shutdown': ['25', 'Reason']}, 'path': ['path1']}]
    event = runner.base.actions.RestartEvent('Some reason', timeout=25)
    action.side_effect = event
    self.assertRaises(SystemExit, self.cr._ProcessTasks, conf)
    restart.assert_called_with(25, 'Some reason')
    self.assertTrue(pop.called)
    pop.reset_mock()
    # with retry
    event = runner.base.actions.RestartEvent(
        'Some other reason', timeout=10, retry_on_restart=True)
    action.side_effect = event
    self.assertRaises(SystemExit, self.cr._ProcessTasks, conf)
    restart.assert_called_with(10, 'Some other reason')
    self.assertFalse(pop.called)

  @mock.patch.object(runner.power, 'Shutdown', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_ProcessAction', autospec=True)
  @mock.patch.object(runner.ConfigRunner, '_PopTask', autospec=True)
  def testShutdownEvents(self, pop, action, shutdown):
    conf = [{'data': {'Restart': ['25', 'Reason']}, 'path': ['path1']}]
    event = runner.base.actions.ShutdownEvent('Some reason', timeout=25)
    action.side_effect = event
    self.assertRaises(SystemExit, self.cr._ProcessTasks, conf)
    shutdown.assert_called_with(25, 'Some reason')
    self.assertTrue(pop.called)
    pop.reset_mock()
    # with retry
    event = runner.base.actions.ShutdownEvent(
        'Some other reason', timeout=10, retry_on_restart=True)
    action.side_effect = event
    self.assertRaises(SystemExit, self.cr._ProcessTasks, conf)
    shutdown.assert_called_with(10, 'Some other reason')
    self.assertFalse(pop.called)


  @mock.patch.object(runner.base.actions, 'SetTimer', autospec=True)
  @mock.patch.object(runner.files, 'Read', autospec=True)
  @mock.patch.object(runner.files, 'Dump', autospec=True)
  def testProcessActions(self, dump, reader, set_timer):
    reader.return_value = [{'data': {'SetTimer': ['TestTimer']},
                            'path': ['/autobuild']}]
    # missing file
    reader.side_effect = runner.files.Error
    self.assertRaises(runner.ConfigRunnerError, self.cr.Start,
                      '/tmp/path/missing.yaml')
    reader.side_effect = None
    # valid command
    self.cr.Start('/tmp/path/tasks.yaml')
    reader.assert_called_with('/tmp/path/tasks.yaml')
    set_timer.assert_called_with(build_info=self.buildinfo, args=['TestTimer'])
    self.assertTrue(set_timer.return_value.Run.called)
    self.assertTrue(dump.called)
    # invalid command
    self.assertRaises(runner.ConfigRunnerError, self.cr._ProcessTasks,
                      [{'data': {'BadSetTimer': ['Timer1']},
                        'path': ['/autobuild']}])
    # action error
    set_timer.side_effect = runner.base.actions.ActionError
    self.assertRaises(runner.ConfigRunnerError, self.cr._ProcessTasks,
                      [{'data': {'SetTimer': ['Timer1']},
                        'path': ['/autobuild']}])


if __name__ == '__main__':
  basetest.main()
