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

from unittest import mock

from absl.testing import absltest
from glazier.lib.actions import drivers
from glazier.lib.buildinfo import BuildInfo


class DriversTest(absltest.TestCase):

  @mock.patch.object(BuildInfo, 'ReleasePath')
  @mock.patch('glazier.lib.download.Download.VerifyShaHash', autospec=True)
  @mock.patch('glazier.lib.download.Download.DownloadFile', autospec=True)
  @mock.patch.object(drivers.execute, 'execute_binary', autospec=True)
  @mock.patch.object(drivers.file_util, 'CreateDirectories', autospec=True)
  def test_driver_wim(
      self, mock_createdirectories, mock_execute_binaries, mock_downloadfile,
      mock_verifyshahash, mock_releasepath):
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
    mock_releasepath.return_value = '/'

    # Success
    dw = drivers.DriverWIM(conf['data']['driver'], bi)
    dw.Run()
    mock_downloadfile.assert_called_with(
        mock.ANY, ('https://glazier-server.example.com/'
                   'bin/Drivers/Lenovo/W54x-Win10-Storage.wim'),
        local,
        show_progress=True)
    mock_verifyshahash.assert_called_with(mock.ANY, local, sha_256)
    cache = drivers.constants.SYS_CACHE
    mock_execute_binaries.assert_called_with(
        f'{drivers.constants.WINPE_SYSTEM32}/dism.exe', [
            '/Unmount-Image', f'/MountDir:{cache}\\Drivers\\',
            '/Discard'
        ],
        shell=True)
    mock_createdirectories.assert_called_with('%s\\Drivers\\' % cache)

    # Invalid format
    conf['data']['driver'][0][1] = 'C:\\W54x-Win10-Storage.zip'
    dw = drivers.DriverWIM(conf['data']['driver'], bi)
    with self.assertRaises(drivers.ActionError):
      dw.Run()
    conf['data']['driver'][0][1] = 'C:\\W54x-Win10-Storage.wim'

    # Mount Fail
    mock_execute_binaries.side_effect = drivers.execute.Error
    with self.assertRaises(drivers.ActionError):
      dw.Run()
    # Dism Fail
    mock_execute_binaries.side_effect = iter([0, drivers.execute.Error])
    with self.assertRaises(drivers.ActionError):
      dw.Run()
    # Unmount Fail
    mock_execute_binaries.side_effect = iter([0, 0, drivers.execute.Error])
    with self.assertRaises(drivers.ActionError):
      dw.Run()

  # TODO(b/237812617): Parameterize this test.
  def test_driver_wim_validate(self):
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
  absltest.main()
