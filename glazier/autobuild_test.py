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


from unittest import mock

from absl.testing import absltest
from glazier import autobuild
from glazier.lib import buildinfo
from glazier.lib import test_utils
from glazier.lib import title
from glazier.lib import winpe

from glazier.lib import errors


class AutobuildTest(test_utils.GlazierTestCase):

  @mock.patch.object(autobuild, 'logs', autospec=True)
  def setUp(self, logs):
    super(AutobuildTest, self).setUp()
    self.autobuild = autobuild.AutoBuild()
    autobuild.logging = logs.logging

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_setup_task_list(self, mock_check_winpe):
    # Host
    tasklist = autobuild.constants.SYS_TASK_LIST
    mock_check_winpe.return_value = False
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    autobuild.FLAGS.preserve_tasks = True
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)

    # WinPE
    self.patch_constant_file_path(autobuild.constants, 'WINPE_TASK_LIST')
    mock_check_winpe.return_value = True
    tasklist = autobuild.constants.WINPE_TASK_LIST
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    self.assertTrue(autobuild.os.path.exists(tasklist))
    autobuild.FLAGS.preserve_tasks = False
    self.assertEqual(self.autobuild._SetupTaskList(), tasklist)
    self.assertFalse(autobuild.os.path.exists(tasklist))

  @mock.patch.object(autobuild.terminator, 'log_and_exit', autospec=True)
  @mock.patch.object(autobuild, 'os', autospec=True)
  def test_setup_task_list_error(self, mock_os, mock_log_and_exit):
    self.patch_constant_file_path(autobuild.constants, 'SYS_TASK_LIST')
    autobuild.FLAGS.preserve_tasks = False
    mock_os.remove.side_effect = OSError
    self.autobuild._SetupTaskList()
    mock_log_and_exit.assert_called_with(self.autobuild._build_info, mock.ANY)

  @mock.patch.object(autobuild.terminator, 'log_and_exit', autospec=True)
  @mock.patch.object(autobuild.title, 'set_title', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(autobuild.runner, 'ConfigRunner', autospec=True)
  @mock.patch.object(autobuild.builder, 'ConfigBuilder', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BeyondCorp', autospec=True)
  def test_run_build(
      self, mock_beyondcorp, mock_configbuilder, mock_configrunner,
      mock_check_winpe, mock_set_title, mock_log_and_exit):
    mock_beyondcorp.return_value = False
    mock_check_winpe.return_value = False
    self.autobuild.RunBuild()
    self.assertTrue(mock_set_title.called)

    # ConfigBuilderError
    mock_configbuilder.side_effect = autobuild.builder.ConfigBuilderError
    self.autobuild.RunBuild()
    mock_log_and_exit.assert_called_with(self.autobuild._build_info, mock.ANY)

    # ConfigRunnerError
    mock_configbuilder.side_effect = None
    mock_configrunner.side_effect = autobuild.runner.ConfigRunnerError
    self.autobuild.RunBuild()
    mock_log_and_exit.assert_called_with(self.autobuild._build_info, mock.ANY)

  @mock.patch.object(title, 'set_title', autospec=True)
  def test_keyboard_interrupt(self, mock_set_title):
    mock_set_title.side_effect = KeyboardInterrupt
    with self.assertRaises(SystemExit) as cm:
      self.autobuild.RunBuild()
    self.assertEqual(cm.exception.code, 1)
    self.assertTrue(autobuild.logging.info.called)

  @mock.patch.object(autobuild.terminator, 'log_and_exit', autospec=True)
  @mock.patch.object(title, 'set_title', autospec=True)
  def test_glazier_error(self, mock_set_title, mock_log_and_exit):
    mock_set_title.side_effect = errors.GlazierError
    self.autobuild.RunBuild()
    self.assertTrue(mock_log_and_exit.called)

  @mock.patch.object(autobuild.terminator, 'log_and_exit', autospec=True)
  @mock.patch.object(title, 'set_title', autospec=True)
  def test_main_exception(self, mock_set_title, mock_log_and_exit):
    mock_set_title.side_effect = Exception
    self.autobuild.RunBuild()
    mock_log_and_exit.assert_called_with(self.autobuild._build_info, mock.ANY)


if __name__ == '__main__':
  absltest.main()
