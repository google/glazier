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
"""Tests for glazier.lib.actions.installer."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib import events
from glazier.lib import log_copy
from glazier.lib import stage
from glazier.lib import test_utils
from glazier.lib.actions import installer

from glazier.lib import constants


class InstallerTest(test_utils.GlazierTestCase):

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_add_choice(self, mock_buildinfo):
    choice = {
        'type':
            'toggle',
        'prompt':
            'Set system shell to PowerShell',
        'name':
            'core_ps_shell',
        'options': [{
            'tip': '',
            'value': False,
            'label': 'False'
        }, {
            'default': True,
            'tip': '',
            'value': True,
            'label': 'True'
        }]
    }
    a = installer.AddChoice(choice, mock_buildinfo)
    a.Run()
    mock_buildinfo.AddChooserOption.assert_called_with(choice)

  def test_add_choice_validate(self):
    choice = {
        'type':
            'toggle',
        'prompt':
            'Set system shell to PowerShell',
        'name':
            'core_ps_shell',
        'options': [{
            'tip': '',
            'value': False,
            'label': 'False'
        }, {
            'default': True,
            'tip': '',
            'value': True,
            'label': 'True'
        }]
    }
    a = installer.AddChoice(choice, None)
    a.Validate()

    # prompt (name, type)
    choice['name'] = True
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # tip
    choice['name'] = 'core_ps_shell'
    choice['options'][0]['tip'] = True
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # default
    choice['options'][0]['tip'] = ''
    choice['options'][0]['default'] = 3
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # label
    choice['options'][0]['default'] = True
    choice['options'][0]['label'] = False
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # value
    choice['options'][0]['label'] = 'False'
    choice['options'][0]['value'] = []
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # options dict
    choice['options'][0] = False
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    # options list
    choice['options'] = False
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    del choice['name']
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

    a = installer.AddChoice(False, None)
    with self.assert_raises_with_validation(installer.ValidationError):
      a.Validate()

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_build_info_dump(self, mock_buildinfo):
    d = installer.BuildInfoDump(None, mock_buildinfo)
    d.Run()
    mock_buildinfo.Serialize.assert_called_with(
        '{}/build_info.yaml'.format(constants.SYS_CACHE))

  @mock.patch.object(installer.registry, 'set_value', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_build_info_save(self, mock_buildinfo, mock_set_value):

    timer_root = r'{0}\{1}'.format(constants.REG_ROOT, 'Timers')
    temp_cache_dir = self.create_tempdir()
    self.patch_constant(constants, 'SYS_CACHE', temp_cache_dir.full_path)
    temp_cache_dir.create_file(
        file_path='build_info.yaml',
        content='{BUILD: {opt 1: true, TIMER_opt 2: some value, opt 3: 12345}}\n'
    )
    s = installer.BuildInfoSave(None, mock_buildinfo)
    s.Run()

    mock_set_value.assert_has_calls(
        [
            mock.call('opt 1', True, 'HKLM', constants.REG_ROOT),
            mock.call('TIMER_opt 2', 'some value', 'HKLM', timer_root),
            mock.call('opt 3', 12345, 'HKLM', constants.REG_ROOT),
        ],
        any_order=True)
    s.Run()

  @mock.patch.object(installer.logging, 'debug', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_build_info_save_error(self, mock_buildinfo, mock_debug):
    installer.BuildInfoSave(None, mock_buildinfo).Run()
    mock_debug.assert_called_with(
        '%s does not exist - skipped processing.',
        '{}/build_info.yaml'.format(constants.SYS_CACHE))

  def test_change_server(self):
    build_info = buildinfo.BuildInfo()
    d = installer.ChangeServer(
        ['http://new-server.example.com', '/new/conf/root'], build_info)
    with self.assert_raises_with_validation(events.ServerChangeEvent):
      d.Run()
    self.assertEqual(build_info.ConfigServer(), 'http://new-server.example.com')
    self.assertEqual(build_info.ActiveConfigPath(), '/new/conf/root')

  @mock.patch.object(installer.file_system, 'CopyFile', autospec=True)
  def test_exit_win_pe(self, mock_copyfile):
    cache = constants.SYS_CACHE
    ex = installer.ExitWinPE(None, None)
    with self.assert_raises_with_validation(events.RestartEvent):
      ex.Run()
    mock_copyfile.assert_has_calls([
        mock.call(['/task_list.yaml',
                   '%s/task_list.yaml' % cache], mock.ANY),
    ])
    mock_copyfile.return_value.Run.assert_called()

  @mock.patch.object(installer.log_copy, 'LogCopy', autospec=True)
  def test_log_copy(self, mock_logcopy):

    log_file = r'X:\glazier.log'
    log_host = 'log-server.example.com'

    # copy eventlog
    lc = installer.LogCopy([log_file], None)
    lc.Run()
    mock_logcopy.return_value.EventLogCopy.assert_called_with(log_file)
    self.assertFalse(mock_logcopy.return_value.ShareCopy.called)
    mock_logcopy.reset_mock()

    # copy both
    lc = installer.LogCopy([log_file, log_host], None)
    lc.Run()
    mock_logcopy.return_value.EventLogCopy.assert_called_with(log_file)
    mock_logcopy.return_value.ShareCopy.assert_called_with(log_file, log_host)
    mock_logcopy.reset_mock()

    # copy errors
    mock_logcopy.return_value.EventLogCopy.side_effect = log_copy.LogCopyError(
        'fail')
    mock_logcopy.return_value.ShareCopy.side_effect = log_copy.LogCopyError(
        'fail')
    lc.Run()
    mock_logcopy.return_value.EventLogCopy.assert_called_with(log_file)
    mock_logcopy.return_value.ShareCopy.assert_called_with(log_file, log_host)

  def test_log_copy_validate(self):
    log_host = 'log-server.example.com'
    lc = installer.LogCopy(r'X:\glazier.log', None)
    with self.assert_raises_with_validation(installer.ValidationError):
      lc.Validate()
    lc = installer.LogCopy([1, 2, 3], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      lc.Validate()
    lc = installer.LogCopy([1], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      lc.Validate()
    lc = installer.LogCopy([r'X:\glazier.log'], None)
    lc.Validate()
    lc = installer.LogCopy([r'X:\glazier.log', log_host], None)
    lc.Validate()

  @mock.patch.object(installer.time, 'sleep', autospec=True)
  def test_sleep(self, sleep):
    s = installer.Sleep([1520], None)
    s.Run()
    sleep.assert_called_with(1520)

  @mock.patch.object(installer.time, 'sleep', autospec=True)
  def test_sleep_string(self, sleep):
    s = installer.Sleep([1234, 'Some Reason.'], None)
    s.Run()
    sleep.assert_called_with(1234)

  def test_sleep_validate(self):
    s = installer.Sleep('30', None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.Sleep([1, 2, 3], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.Sleep(['30'], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.Sleep([30], None)
    s.Validate()
    s = installer.Sleep([30, 'Some reason.'], None)
    s.Validate()

  @mock.patch.object(installer.chooser, 'Chooser', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_show_chooser(self, build_info, chooser):
    c = installer.ShowChooser(None, build_info)
    c.Run()
    self.assertTrue(chooser.return_value.Display.called)
    self.assertTrue(chooser.return_value.Display.called)
    build_info.StoreChooserResponses.assert_called_with(
        chooser.return_value.Responses.return_value)
    self.assertTrue(build_info.FlushChooserOptions.called)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  def test_start_stage(self, set_stage):
    s = installer.StartStage([1], None)
    s.Run()
    set_stage.assert_called_with(1)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  @mock.patch.object(installer.stage, 'exit_stage', autospec=True)
  def test_start_non_terminal_stage(self, exit_stage, set_stage):
    installer.StartStage([50, False], None).Run()
    set_stage.assert_called_with(50)
    self.assertFalse(exit_stage.called)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  @mock.patch.object(installer.stage, 'exit_stage', autospec=True)
  def test_start_terminal_stage(self, exit_stage, set_stage):
    installer.StartStage([100, True], None).Run()
    set_stage.assert_called_with(100)
    exit_stage.assert_called_with(100)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  def test_start_stage_exception(self, set_stage):
    set_stage.side_effect = stage.Error('Test')
    ss = installer.StartStage([2], None)
    with self.assert_raises_with_validation(installer.ActionError):
      ss.Run()

  def test_start_stage_validate(self):
    s = installer.StartStage('30', None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.StartStage([1, 2, 3], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.StartStage(['30'], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.StartStage([30, 'Hello'], None)
    with self.assert_raises_with_validation(installer.ValidationError):
      s.Validate()
    s = installer.StartStage([30], None)
    s.Validate()


if __name__ == '__main__':
  absltest.main()
