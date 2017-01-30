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

"""Tests for glazier.lib.actions.drivers."""

from glazier.lib.actions import drivers
from glazier.lib.buildinfo import BuildInfo
import mock
from google.apputils import basetest


class DriversTest(basetest.TestCase):

  @mock.patch.object(BuildInfo, 'ReleasePath')
  @mock.patch('glazier.lib.download.Download.VerifyShaHash', autospec=True)
  @mock.patch('glazier.lib.download.Download.DownloadFile', autospec=True)
  @mock.patch.object(drivers, 'Execute', autospec=True)
  @mock.patch.object(drivers.file_util, 'CreateDirectories', autospec=True)
  def testDriverWIM(self, mkdir, exe, dl, sha, rpath):
    bi = BuildInfo()
    # Setup
    remote = '@Drivers/Lenovo/W54x-Win10-Storage.wim'
    local = r'c:\W54x-Win10-Storage.wim'
    sha_256 = (
        'D30F9DB0698C87901DF6824D11203BDC2D6DAAF0CE14ABD7C0A7B75974936748')
    conf = {
        'data': {
            'driver': [[remote, local, sha_256]]
        },
        'path': ['/autobuild']
    }
    rpath.return_value = '/'

    # Success
    dw = drivers.DriverWIM(conf['data']['driver'], bi)
    dw.Run()
    dl.assert_called_with(
        mock.ANY, ('https://glazier-server.example.com/'
                   'bin/Drivers/Lenovo/W54x-Win10-Storage.wim'),
        local,
        show_progress=True)
    sha.assert_called_with(mock.ANY, local, sha_256)
    cache = drivers.constants.SYS_CACHE
    exe.assert_called_with([[('X:\\Windows\\System32\\dism.exe /Unmount-Image '
                              '/MountDir:%s\\Drivers\\ /Discard' % cache)]],
                           mock.ANY)
    mkdir.assert_called_with('%s\\Drivers\\' % cache)

    # Invalid format
    conf['data']['driver'][0][1] = 'C:\\W54x-Win10-Storage.zip'
    dw = drivers.DriverWIM(conf['data']['driver'], bi)
    self.assertRaises(drivers.ActionError, dw.Run)
    conf['data']['driver'][0][1] = 'C:\\W54x-Win10-Storage.wim'

    # Mount Fail
    exe.return_value.Run.side_effect = drivers.ActionError()
    self.assertRaises(drivers.ActionError, dw.Run)
    # Dism Fail
    exe.return_value.Run.side_effect = iter([0, drivers.ActionError()])
    self.assertRaises(drivers.ActionError, dw.Run)
    # Unmount Fail
    exe.return_value.Run.side_effect = iter([0, 0, drivers.ActionError()])
    self.assertRaises(drivers.ActionError, dw.Run)

  def testDriverWIMValidate(self):
    g = drivers.DriverWIM('String', None)
    self.assertRaises(drivers.ValidationError, g.Validate)
    g = drivers.DriverWIM([[1, 2, 3]], None)
    self.assertRaises(drivers.ValidationError, g.Validate)
    g = drivers.DriverWIM([[1, '/tmp/out/path']], None)
    self.assertRaises(drivers.ValidationError, g.Validate)
    g = drivers.DriverWIM([['/tmp/src.zip', 2]], None)
    self.assertRaises(drivers.ValidationError, g.Validate)
    g = drivers.DriverWIM([['https://glazier/bin/src.wim', '/tmp/out/src.zip']],
                          None)
    self.assertRaises(drivers.ValidationError, g.Validate)
    g = drivers.DriverWIM([['https://glazier/bin/src.wim', '/tmp/out/src.wim']],
                          None)
    g.Validate()
    g = drivers.DriverWIM(
        [['https://glazier/bin/src.wim', '/tmp/out/src.wim', '12345']], None)
    g.Validate()
    g = drivers.DriverWIM(
        [['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345', '67890']],
        None)
    self.assertRaises(drivers.ValidationError, g.Validate)


if __name__ == '__main__':
  basetest.main()
