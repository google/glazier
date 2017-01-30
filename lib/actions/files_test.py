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

"""Tests for glazier.lib.actions.files."""

from pyfakefs import fake_filesystem
from pyfakefs import fake_filesystem_shutil
from glazier.lib import buildinfo
from glazier.lib.actions import files
import mock
from google.apputils import basetest


class FilesTest(basetest.TestCase):

  def setUp(self):
    self.filesystem = fake_filesystem.FakeFilesystem()
    files.open = fake_filesystem.FakeFileOpen(self.filesystem)
    files.file_util.shutil = fake_filesystem_shutil.FakeShutilModule(
        self.filesystem)

  @mock.patch.object(files.time, 'sleep', autospec=True)
  @mock.patch.object(files.cache.Cache, 'CacheFromLine', autospec=True)
  @mock.patch.object(files.subprocess, 'call', autospec=True)
  def testExecute(self, call, cache, sleep):
    bi = buildinfo.BuildInfo()
    cache.side_effect = iter(['cmd.exe /c', 'explorer.exe'])
    e = files.Execute([['cmd.exe /c', [0]], ['explorer.exe']], bi)
    call.return_value = 0
    e.Run()
    call.assert_has_calls([mock.call(
        'cmd.exe /c', shell=True), mock.call(
            'explorer.exe', shell=True)])
    self.assertTrue(sleep.called)

    # success codes
    cache.side_effect = None
    cache.return_value = 'cmd.exe /c script.bat'
    e = files.Execute([['cmd.exe /c script.bat', [2, 4]]], bi)
    self.assertRaises(files.ActionError, e.Run)
    call.return_value = 4
    e.Run()

    # reboot codes - no retry
    e = files.Execute([['cmd.exe /c script.bat', [0], [2, 4]]], bi)
    with self.assertRaises(files.RestartEvent) as r_evt:
      e.Run()
      self.assertEqual(r_evt.retry_on_restart, False)

    # reboot codes -  retry
    e = files.Execute([['cmd.exe /c #script.bat', [0], [2, 4], True]], bi)
    with self.assertRaises(files.RestartEvent) as r_evt:
      e.Run()
      self.assertEqual(r_evt.retry_on_restart, True)
    cache.assert_called_with(mock.ANY, 'cmd.exe /c #script.bat', bi)
    call.assert_called_with('cmd.exe /c script.bat', shell=True)

    # WindowsError
    files.WindowsError = Exception
    call.side_effect = files.WindowsError
    self.assertRaises(files.ActionError, e.Run)
    # KeyboardInterrupt
    call.side_effect = KeyboardInterrupt
    e = files.Execute([['cmd.exe /c', [0]], ['explorer.exe']], bi)
    e.Run()
    # Cache error
    call.side_effect = None
    call.return_value = 0
    cache.side_effect = files.cache.CacheError
    self.assertRaises(files.ActionError, e.Run)

  def testExecuteValidation(self):
    e = files.Execute([['cmd.exe', [0], [2], False], ['explorer.exe']], None)
    e.Validate()
    e = files.Execute([[]], None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute(['explorer.exe'], None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute('explorer.exe', None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0]], ['explorer.exe', '0']], None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0]], ['explorer.exe', ['0']]], None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0], ['2']], ['explorer.exe']], None)
    self.assertRaises(files.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0], [2], 'True'], ['explorer.exe']], None)
    self.assertRaises(files.ValidationError, e.Validate)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def testGet(self, verify, down_file, r_path):
    bi = buildinfo.BuildInfo()
    r_path.return_value = 'https://glazier-server.example.com/'
    remote = '@glazier/1.0/autobuild.par'
    local = r'/tmp/autobuild.par'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.filesystem.CreateFile(
        r'/tmp/autobuild.par.sha256', contents=test_sha256)
    down_file.return_value = True
    conf = [[remote, local]]
    g = files.Get(conf, bi)
    g.Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/bin/glazier/1.0/autobuild.par',
        local,
        show_progress=True)
    # Relative Paths
    conf = [['autobuild.bat', '/tmp/autobuild.bat']]
    g = files.Get(conf, bi)
    g.Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/autobuild.bat',
        '/tmp/autobuild.bat',
        show_progress=True)
    down_file.return_value = None
    # DownloadError
    err = files.download.DownloadError('Error')
    down_file.side_effect = err
    g = files.Get([[remote, local]], bi)
    self.assertRaises(files.ActionError, g.Run)
    down_file.side_effect = None
    # file_util.Error
    self.filesystem.CreateFile('/directory')
    g = files.Get([[remote, '/directory/file.txt']], bi)
    self.assertRaises(files.ActionError, g.Run)
    # good hash
    verify.return_value = True
    g = files.Get([[remote, local, test_sha256]], bi)
    g.Run()
    verify.assert_called_with(mock.ANY, local, test_sha256)
    # bad hash
    verify.return_value = False
    g = files.Get([[remote, local, test_sha256]], bi)
    self.assertRaises(files.ActionError, g.Run)
    # none hash
    verify.reset_mock()
    conf = [[remote, local, '']]
    g = files.Get(conf, bi)
    g.Run()
    self.assertFalse(verify.called)

  def testGetValidate(self):
    g = files.Get('String', None)
    self.assertRaises(files.ValidationError, g.Validate)
    g = files.Get([[1, 2, 3]], None)
    self.assertRaises(files.ValidationError, g.Validate)
    g = files.Get([[1, '/tmp/out/path']], None)
    self.assertRaises(files.ValidationError, g.Validate)
    g = files.Get([['/tmp/src.zip', 2]], None)
    self.assertRaises(files.ValidationError, g.Validate)
    g = files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip']], None)
    g.Validate()
    g = files.Get(
        [['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345']], None)
    g.Validate()
    g = files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345',
                    '67890']], None)
    self.assertRaises(files.ValidationError, g.Validate)

  @mock.patch.object(files.file_util, 'CreateDirectories', autospec=True)
  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testUnzip(self, build_info, create_dir):
    src = '/tmp/input.zip'
    dst = '/out/dir/path'
    # bad args
    un = files.Unzip([], build_info)
    self.assertRaises(files.ActionError, un.Run)
    un = files.Unzip([src], build_info)
    self.assertRaises(files.ActionError, un.Run)
    # bad path
    un = files.Unzip([src, dst], build_info)
    self.assertRaises(files.ActionError, un.Run)
    # create error
    create_dir.side_effect = files.file_util.Error
    self.assertRaises(files.ActionError, un.Run)
    # good
    create_dir.side_effect = None
    with mock.patch.object(files.zipfile, 'ZipFile', autospec=True) as z:
      un = files.Unzip([src, dst], build_info)
      un.Run()
      z.assert_called_with(src)
      z.return_value.extractall.assert_called_with(dst)
      create_dir.assert_called_with(dst)

  def testUnzipValidate(self):
    un = files.Unzip('String', None)
    self.assertRaises(files.ValidationError, un.Validate)
    un = files.Unzip([1, 2, 3], None)
    self.assertRaises(files.ValidationError, un.Validate)
    un = files.Unzip([1, '/tmp/out/path'], None)
    self.assertRaises(files.ValidationError, un.Validate)
    un = files.Unzip(['/tmp/src.zip', 2], None)
    self.assertRaises(files.ValidationError, un.Validate)
    un = files.Unzip(['/tmp/src.zip', '/tmp/out/path'], None)
    un.Validate()


if __name__ == '__main__':
  basetest.main()
