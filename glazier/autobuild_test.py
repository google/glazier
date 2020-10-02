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

from absl.testing import absltest

from glazier import autobuild
from glazier.lib import buildinfo
from glazier.lib import title
from glazier.lib import winpe

import mock
from pyfakefs import fake_filesystem


class LogFatalError(Exception):
  pass


class BuildInfoTest(absltest.TestCase):

  @mock.patch.object(autobuild, 'logs', autospec=True)
  def setUp(self, logs):
    super(BuildInfoTest, self).setUp()
    self.autobuild = autobuild.AutoBuild()
    autobuild.logging = logs.logging
    autobuild.logging.fatal.side_effect = LogFatalError()
    self.filesystem = fake_filesystem.FakeFilesystem()
    autobuild.os = fake_filesystem.FakeOsModule(self.filesystem)

  def testLogFatal(self):
    with self.assertRaises(LogFatalError):
      autobuild._LogFatal('image failed', buildinfo.BuildInfo(), collect=False)
    autobuild.logging.fatal.assert_called_with(f'{autobuild._FAILURE_MSG}',
                                               'image failed')

  def testLogFatalCode(self):
    with self.assertRaises(LogFatalError):
      autobuild._LogFatal('image failed', buildinfo.BuildInfo(), 1234, False)
    autobuild.logging.fatal.assert_called_with(f'{autobuild._FAILURE_MSG}#1234',
                                               'image failed')

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def testSetupTaskList(self, wpe):
    # Host
    tasklist = autobuild.constants.SYS_TASK_LIST
    wpe.return_value = False
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    autobuild.FLAGS.preserve_tasks = True
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)

    # WinPE
    self.filesystem.create_file(autobuild.constants.WINPE_TASK_LIST)
    wpe.return_value = True
    tasklist = autobuild.constants.WINPE_TASK_LIST
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    self.assertTrue(autobuild.os.path.exists(tasklist))
    autobuild.FLAGS.preserve_tasks = False
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    self.assertFalse(autobuild.os.path.exists(tasklist))

  @mock.patch.object(autobuild, '_LogFatal', autospec=True)
  @mock.patch.object(autobuild.title, 'set_title', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(autobuild.runner, 'ConfigRunner', autospec=True)
  @mock.patch.object(autobuild.builder, 'ConfigBuilder', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BeyondCorp', autospec=True)
  def testRunBuild(self, bc, builder, runner, wpe, st, fatal):
    bc.return_value = False
    wpe.return_value = False
    self.autobuild.RunBuild()
    self.assertTrue(st.called)

    # ConfigBuilderError
    builder.side_effect = autobuild.builder.ConfigBuilderError
    self.autobuild.RunBuild()
    fatal.assert_called_with(mock.ANY, self.autobuild._build_info)
    # ConfigRunnerError
    builder.side_effect = None
    runner.side_effect = autobuild.runner.ConfigRunnerError
    self.autobuild.RunBuild()
    fatal.assert_called_with(mock.ANY, self.autobuild._build_info)

  @mock.patch.object(title, 'set_title', autospec=True)
  def testKeyboardInterrupt(self, st):
    st.side_effect = KeyboardInterrupt
    with self.assertRaises(SystemExit) as cm:
      self.autobuild.RunBuild()
    self.assertEqual(cm.exception.code, 1)
    self.assertTrue(autobuild.logging.info.called)

  @mock.patch.object(autobuild, '_LogFatal', autospec=True)
  @mock.patch.object(title, 'set_title', autospec=True)
  def testMainException(self, st, fatal):
    st.side_effect = Exception
    self.autobuild.RunBuild()
    fatal.assert_called_with(mock.ANY, self.autobuild._build_info, 4000)


if __name__ == '__main__':
  absltest.main()
