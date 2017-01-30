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

"""Unit tests for autobuild."""

from pyfakefs import fake_filesystem
from glazier import autobuild
import mock
from google.apputils import basetest


class LogFatal(Exception):
  pass


class BuildInfoTest(basetest.TestCase):

  @mock.patch.object(autobuild, 'logs', autospec=True)
  def setUp(self, logs):
    self.autobuild = autobuild.AutoBuild()
    autobuild.logging = logs.logging
    autobuild.logging.fatal.side_effect = LogFatal()

  def testLogFatal(self):
    self.assertRaises(LogFatal, self.autobuild._LogFatal,
                      'failure is always an option')
    self.assertTrue(autobuild.logging.fatal.called)

  def testSetupTaskList(self):
    cache = autobuild.constants.SYS_CACHE
    filesystem = fake_filesystem.FakeFilesystem()
    filesystem.CreateFile(r'X:\task_list.yaml')
    autobuild.os = fake_filesystem.FakeOsModule(filesystem)
    self.assertEqual(self.autobuild._SetupTaskList(),
                     '%s\\task_list.yaml' % cache)
    autobuild.FLAGS.preserve_tasks = True
    self.assertEqual(self.autobuild._SetupTaskList(),
                     '%s\\task_list.yaml' % cache)
    autobuild.FLAGS.environment = 'WinPE'
    self.assertEqual(self.autobuild._SetupTaskList(), r'X:\task_list.yaml')
    self.assertTrue(autobuild.os.path.exists(r'X:\task_list.yaml'))
    autobuild.FLAGS.preserve_tasks = False
    self.assertEqual(self.autobuild._SetupTaskList(), r'X:\task_list.yaml')
    self.assertFalse(autobuild.os.path.exists(r'X:\task_list.yaml'))

  @mock.patch.object(autobuild.runner, 'ConfigRunner', autospec=True)
  @mock.patch.object(autobuild.builder, 'ConfigBuilder', autospec=True)
  def testRunBuild(self, builder, runner):
    self.autobuild.RunBuild()
    # ConfigBuilderError
    builder.side_effect = autobuild.builder.ConfigBuilderError
    self.assertRaises(LogFatal, self.autobuild.RunBuild)
    # ConfigRunnerError
    builder.side_effect = None
    runner.side_effect = autobuild.runner.ConfigRunnerError
    self.assertRaises(LogFatal, self.autobuild.RunBuild)


if __name__ == '__main__':
  basetest.main()
