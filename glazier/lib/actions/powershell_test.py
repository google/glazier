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

"""Tests for glazier.lib.actions.powershell."""

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib.actions import powershell
import mock


class PowershellTest(absltest.TestCase):

  def setUp(self):
    super(PowershellTest, self).setUp()
    buildinfo.constants.FLAGS.config_server = 'https://glazier/'

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunLocal', autospec=True)
  @mock.patch.object(powershell.cache.Cache, 'CacheFromLine', autospec=True)
  def testPSScript(self, cache, run):
    bi = buildinfo.BuildInfo()
    cache.return_value = r'C:\Cache\Some-Script.ps1'
    ps = powershell.PSScript(['#Some-Script.ps1', ['-Flag1']], bi)
    ps.Run()
    cache.assert_called_with(mock.ANY, '#Some-Script.ps1', bi)
    run.assert_called_with(
        mock.ANY, r'C:\Cache\Some-Script.ps1', args=['-Flag1'])
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(powershell.ActionError, ps.Run)
    # Cache error
    run.side_effect = None
    cache.side_effect = powershell.cache.CacheError
    self.assertRaises(powershell.ActionError, ps.Run)

  def testPSScriptValidate(self):
    ps = powershell.PSScript(30, None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSScript([], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSScript([30, 40], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSScript(['#Some-Script.ps1'], None)
    ps.Validate()
    ps = powershell.PSScript(['#Some-Script.ps1', '-Flags'], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSScript(['#Some-Script.ps1', ['-Flags']], None)
    ps.Validate()

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommand(self, run):
    bi = buildinfo.BuildInfo()
    ps = powershell.PSCommand(['Write-Verbose Foo -Verbose', [1337]],
                              bi)
    ps.Run()
    run.assert_called_with(
        mock.ANY, ['Write-Verbose', 'Foo', '-Verbose'], [1337])

  @mock.patch.object(
      powershell.powershell.PowerShell, 'RunCommand', autospec=True)
  def testPSCommandError(self, run):
    ps = powershell.PSCommand(['Write-Verbose Foo -Verbose', [1337]], None)
    run.side_effect = powershell.powershell.PowerShellError
    self.assertRaises(powershell.ActionError, ps.Run)

  def testPSCommandValidate(self):
    ps = powershell.PSCommand(30, None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSCommand([], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSCommand([30, 40], None)
    self.assertRaises(powershell.ValidationError, ps.Validate)
    ps = powershell.PSCommand(['Write-Verbose Foo -Verbose'], None)
    ps.Validate()
    ps = powershell.PSCommand(['Write-Verbose Foo -Verbose', [1337]],
                              None)
    ps.Validate()

if __name__ == '__main__':
  absltest.main()
