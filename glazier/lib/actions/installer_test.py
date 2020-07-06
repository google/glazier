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


from absl.testing import absltest
from pyfakefs import fake_filesystem
from glazier.lib import buildinfo
from glazier.lib import stage
from glazier.lib.actions import installer
import mock


class InstallerTest(absltest.TestCase):

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def testAddChoice(self, build_info):
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
    a = installer.AddChoice(choice, build_info)
    a.Run()
    build_info.AddChooserOption.assert_called_with(choice)

  def testAddChoiceValidate(self):
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
    self.assertRaises(installer.ValidationError, a.Validate)
    # tip
    choice['name'] = 'core_ps_shell'
    choice['options'][0]['tip'] = True
    self.assertRaises(installer.ValidationError, a.Validate)
    # default
    choice['options'][0]['tip'] = ''
    choice['options'][0]['default'] = 3
    self.assertRaises(installer.ValidationError, a.Validate)
    # label
    choice['options'][0]['default'] = True
    choice['options'][0]['label'] = False
    self.assertRaises(installer.ValidationError, a.Validate)
    # value
    choice['options'][0]['label'] = 'False'
    choice['options'][0]['value'] = []
    self.assertRaises(installer.ValidationError, a.Validate)
    # options dict
    choice['options'][0] = False
    self.assertRaises(installer.ValidationError, a.Validate)
    # options list
    choice['options'] = False
    self.assertRaises(installer.ValidationError, a.Validate)
    del choice['name']
    self.assertRaises(installer.ValidationError, a.Validate)
    a = installer.AddChoice(False, None)
    self.assertRaises(installer.ValidationError, a.Validate)

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def testBuildInfoDump(self, build_info):
    d = installer.BuildInfoDump(None, build_info)
    d.Run()
    build_info.Serialize.assert_called_with('{}/build_info.yaml'.format(
        installer.constants.SYS_CACHE))

  @mock.patch.object(installer.registry, 'set_value', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def testBuildInfoSave(self, build_info, sv):
    fs = fake_filesystem.FakeFilesystem()
    installer.open = fake_filesystem.FakeFileOpen(fs)
    installer.os = fake_filesystem.FakeOsModule(fs)
    timer_root = r'{0}\{1}'.format(installer.constants.REG_ROOT, 'Timers')
    fs.CreateFile(
        '{}/build_info.yaml'.format(installer.constants.SYS_CACHE),
        contents='{BUILD: {opt 1: true, TIMER_opt 2: some value, opt 3: 12345}}\n'
    )
    s = installer.BuildInfoSave(None, build_info)
    s.Run()
    sv.assert_has_calls([
        mock.call('opt 1', True, 'HKLM', installer.constants.REG_ROOT),
        mock.call('TIMER_opt 2', 'some value', 'HKLM', timer_root),
        mock.call('opt 3', 12345, 'HKLM', installer.constants.REG_ROOT),
    ],
                        any_order=True)
    s.Run()

  @mock.patch.object(installer.logging, 'debug', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def testBuildInfoSaveError(self, build_info, d):
    installer.BuildInfoSave(None, build_info).Run()
    d.assert_called_with(
        '%s does not exist - skipped processing.',
        '{}/build_info.yaml'.format(installer.constants.SYS_CACHE))

  def testChangeServer(self):
    build_info = buildinfo.BuildInfo()
    d = installer.ChangeServer(
        ['http://new-server.example.com', '/new/conf/root'], build_info)
    self.assertRaises(installer.ServerChangeEvent, d.Run)
    self.assertEqual(build_info.ConfigServer(), 'http://new-server.example.com')
    self.assertEqual(build_info.ActiveConfigPath(), '/new/conf/root')

  @mock.patch.object(installer.file_system, 'CopyFile', autospec=True)
  def testExitWinPE(self, copy):
    cache = installer.constants.SYS_CACHE
    ex = installer.ExitWinPE(None, None)
    with self.assertRaises(installer.RestartEvent):
      ex.Run()
    copy.assert_has_calls([
        mock.call([r'X:\task_list.yaml',
                   '%s\\task_list.yaml' % cache], mock.ANY),
    ])
    copy.return_value.Run.assert_called()

  @mock.patch.object(installer.log_copy, 'LogCopy', autospec=True)
  def testLogCopy(self, copy):
    log_file = r'X:\glazier.log'
    log_host = 'log-server.example.com'
    # copy eventlog
    lc = installer.LogCopy([log_file], None)
    lc.Run()
    copy.return_value.EventLogCopy.assert_called_with(log_file)
    self.assertFalse(copy.return_value.ShareCopy.called)
    copy.reset_mock()
    # copy both
    lc = installer.LogCopy([log_file, log_host], None)
    lc.Run()
    copy.return_value.EventLogCopy.assert_called_with(log_file)
    copy.return_value.ShareCopy.assert_called_with(log_file, log_host)
    copy.reset_mock()
    # copy errors
    copy.return_value.EventLogCopy.side_effect = installer.log_copy.LogCopyError
    copy.return_value.ShareCopy.side_effect = installer.log_copy.LogCopyError
    lc.Run()
    copy.return_value.EventLogCopy.assert_called_with(log_file)
    copy.return_value.ShareCopy.assert_called_with(log_file, log_host)

  def testLogCopyValidate(self):
    log_host = 'log-server.example.com'
    lc = installer.LogCopy(r'X:\glazier.log', None)
    self.assertRaises(installer.ValidationError, lc.Validate)
    lc = installer.LogCopy([1, 2, 3], None)
    self.assertRaises(installer.ValidationError, lc.Validate)
    lc = installer.LogCopy([1], None)
    self.assertRaises(installer.ValidationError, lc.Validate)
    lc = installer.LogCopy([r'X:\glazier.log'], None)
    lc.Validate()
    lc = installer.LogCopy([r'X:\glazier.log', log_host], None)
    lc.Validate()

  @mock.patch.object(installer.time, 'sleep', autospec=True)
  def testSleep(self, sleep):
    s = installer.Sleep([1520], None)
    s.Run()
    sleep.assert_called_with(1520)

  @mock.patch.object(installer.time, 'sleep', autospec=True)
  def testSleepString(self, sleep):
    s = installer.Sleep([1234, 'Some Reason.'], None)
    s.Run()
    sleep.assert_called_with(1234)

  def testSleepValidate(self):
    s = installer.Sleep('30', None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.Sleep([1, 2, 3], None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.Sleep(['30'], None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.Sleep([30], None)
    s.Validate()
    s = installer.Sleep([30, 'Some reason.'], None)
    s.Validate()

  @mock.patch.object(installer.chooser, 'Chooser', autospec=True)
  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def testShowChooser(self, build_info, chooser):
    c = installer.ShowChooser(None, build_info)
    c.Run()
    self.assertTrue(chooser.return_value.Display.called)
    self.assertTrue(chooser.return_value.Display.called)
    build_info.StoreChooserResponses.assert_called_with(
        chooser.return_value.Responses.return_value)
    self.assertTrue(build_info.FlushChooserOptions.called)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  def testStartStage(self, set_stage):
    s = installer.StartStage([1], None)
    s.Run()
    set_stage.assert_called_with(1)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  @mock.patch.object(installer.stage, 'exit_stage', autospec=True)
  def testStartNonTerminalStage(self, exit_stage, set_stage):
    installer.StartStage([50, False], None).Run()
    set_stage.assert_called_with(50)
    self.assertFalse(exit_stage.called)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  @mock.patch.object(installer.stage, 'exit_stage', autospec=True)
  def testStartTerminalStage(self, exit_stage, set_stage):
    installer.StartStage([100, True], None).Run()
    set_stage.assert_called_with(100)
    exit_stage.assert_called_with(100)

  @mock.patch.object(installer.stage, 'set_stage', autospec=True)
  def testStartStageException(self, set_stage):
    set_stage.side_effect = stage.Error('Test')
    ss = installer.StartStage([2], None)
    self.assertRaises(installer.ActionError, ss.Run)

  def testStartStageValidate(self):
    s = installer.StartStage('30', None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.StartStage([1, 2, 3], None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.StartStage(['30'], None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.StartStage([30, 'Hello'], None)
    self.assertRaises(installer.ValidationError, s.Validate)
    s = installer.StartStage([30], None)
    s.Validate()


if __name__ == '__main__':
  absltest.main()
