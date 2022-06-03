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

from unittest import mock

from absl.testing import absltest
from glazier.lib import buildinfo
from glazier.lib.actions import files

from pyfakefs import fake_filesystem
from pyfakefs import fake_filesystem_shutil

from glazier.lib import errors


class FilesTest(absltest.TestCase):

  def setUp(self):
    super(FilesTest, self).setUp()
    self.filesystem = fake_filesystem.FakeFilesystem()
    files.open = fake_filesystem.FakeFileOpen(self.filesystem)
    files.file_util.shutil = fake_filesystem_shutil.FakeShutilModule(
        self.filesystem)
    files.WindowsError = Exception

  # TODO(b/152894756): Split into separate tests.
  @mock.patch.object(files.execute, 'execute_binary', autospec=True)
  @mock.patch.object(files.shlex, 'split', autospec=True)
  @mock.patch.object(files.cache.Cache, 'CacheFromLine', autospec=True)
  def testExecute(self, cache, split, eb):
    bi = buildinfo.BuildInfo()
    cache.side_effect = iter(['cmd.exe /c', 'explorer.exe'])
    eb.return_value = 0
    e = files.Execute([['cmd.exe /c', [0]], ['explorer.exe']], bi)
    e.Run()
    self.assertTrue(split.called)

    # success codes
    cache.side_effect = None
    cache.return_value = 'cmd.exe /c script.bat'
    e = files.Execute([['cmd.exe /c script.bat', [2, 4]]], bi)
    with self.assertRaises(errors.ActionError):
      e.Run()
    eb.return_value = 4
    e.Run()

    # reboot codes - no retry
    e = files.Execute([['cmd.exe /c script.bat', [0], [2, 4]]], bi)
    with self.assertRaises(files.RestartEvent) as cm:
      e.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, False)

    # reboot codes -  retry
    e = files.Execute([['cmd.exe /c #script.bat', [0], [2, 4], True]], bi)
    with self.assertRaises(files.RestartEvent) as cm:
      e.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, True)
    cache.assert_called_with(mock.ANY, 'cmd.exe /c #script.bat', bi)

    # Shell
    files.Execute([['cmd.exe /c #script.bat', [4], [0], True, True]], bi).Run()
    eb.assert_called_with(mock.ANY, mock.ANY, [4, 0], shell=True)

    # KeyboardInterrupt
    eb.side_effect = KeyboardInterrupt
    with self.assertRaises(errors.ActionError):
      e.Run()

    # Execute Error
    eb.side_effect = errors.BinaryExecutionError('some message')
    with self.assertRaises(errors.ActionError):
      e.Run()

    # ValueError
    split.side_effect = ValueError
    with self.assertRaises(errors.ActionError):
      e.Run()

    # Cache error
    cache.side_effect = errors.CacheError('some/file/path')
    with self.assertRaises(errors.ActionError):
      e.Run()

  # TODO(b/152894756): Paramaterize and add cm for these tests
  # (go/python-tips/011).
  def testExecuteValidation(self):
    e = files.Execute([['cmd.exe', [0], [2], False], ['explorer.exe']], None)
    e.Validate()
    e = files.Execute([[]], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute(['explorer.exe'], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute('explorer.exe', None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0]], ['explorer.exe', '0']], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0]], ['explorer.exe', ['0']]], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0], ['2']], ['explorer.exe']], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    e = files.Execute([['cmd.exe', [0], [2], 'True'], ['explorer.exe']], None)
    self.assertRaises(errors.ValidationError, e.Validate)
    with self.assertRaises(errors.ValidationError):
      files.Execute([['cmd.exe', [0], [2], False, 'True'], ['explorer.exe']],
                    None).Validate()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetFromBin(self, down_file, bin_path, rel_path):
    rel_path.return_value = 'https://glazier-server.example.com/'
    bin_path.return_value = 'https://glazier-server.example.com/bin/'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.filesystem.create_file(
        r'/tmp/autobuild.par.sha256', contents=test_sha256)
    down_file.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/bin/glazier/1.0/autobuild.par',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetFromConf(self, down_file, bin_path, rel_path):
    rel_path.return_value = 'https://glazier-server.example.com/'
    bin_path.return_value = 'https://glazier-server.example.com/bin/'
    down_file.return_value = True
    files.Get([['#test/script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/test/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetFromUntagged(self, down_file, bin_path, rel_path):
    rel_path.return_value = 'https://glazier-server.example.com/'
    bin_path.return_value = 'https://glazier-server.example.com/bin/'
    down_file.return_value = True
    files.Get([['test/script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/test/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetFromLocal(self, down_file, bin_path, rel_path):
    rel_path.return_value = 'C:/glazier/conf'
    bin_path.return_value = 'https://glazier-server.example.com/bin/'
    down_file.return_value = True
    files.Get([['#script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    down_file.assert_called_with(
        mock.ANY,
        'C:/glazier/conf/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetDownloadErr(self, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    remote = '@glazier/1.0/autobuild.par'
    local = r'/tmp/autobuild.par'
    down_file.side_effect = errors.DownloadError('Error')
    with self.assertRaises(errors.ActionError):
      files.Get([[remote, local]], buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetMkdirErr(self, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    remote = '@glazier/1.0/autobuild.par'
    self.filesystem.create_file('/directory')
    down_file.side_effect = errors.DownloadError('Error')
    with self.assertRaises(errors.ActionError):
      files.Get([[remote, '/directory/file.txt']], buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def testGetRelativePath(self, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    self.filesystem.create_file(
        r'/tmp/autobuild.par.sha256',
        contents='58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800'
    )
    down_file.return_value = True
    files.Get([['autobuild.bat', '/tmp/autobuild.bat']],
              buildinfo.BuildInfo()).Run()
    down_file.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/autobuild.bat',
        '/tmp/autobuild.bat',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def testGetHashMatch(self, verify, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    local = r'/tmp/autobuild.par'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.filesystem.create_file(
        r'/tmp/autobuild.par.sha256', contents=test_sha256)
    down_file.return_value = True
    verify.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', local, test_sha256]],
              buildinfo.BuildInfo()).Run()
    verify.assert_called_with(mock.ANY, local, test_sha256)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def testGetHashMismatch(self, verify, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.filesystem.create_file(
        r'/tmp/autobuild.par.sha256', contents=test_sha256)
    down_file.return_value = True
    verify.return_value = False
    with self.assertRaises(errors.ActionError):
      files.Get(
          [['@glazier/1.0/autobuild.par', r'/tmp/autobuild.par', test_sha256]],
          buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def testGetNoHash(self, verify, down_file, r_path):
    r_path.return_value = 'https://glazier-server.example.com/'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.filesystem.create_file(
        r'/tmp/autobuild.par.sha256', contents=test_sha256)
    down_file.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', r'/tmp/autobuild.par', '']],
              buildinfo.BuildInfo()).Run()
    self.assertFalse(verify.called)

  def testGetValidate(self):
    with self.assertRaises(errors.ValidationError):
      files.Get('String', None).Validate()
    with self.assertRaises(errors.ValidationError):
      files.Get([[1, 2, 3]], None).Validate()
    with self.assertRaises(errors.ValidationError):
      files.Get([[1, '/tmp/out/path']], None).Validate()
    with self.assertRaises(errors.ValidationError):
      files.Get([['/tmp/src.zip', 2]], None).Validate()
    files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip']],
              None).Validate()
    files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345']],
              None).Validate()
    with self.assertRaises(errors.ValidationError):
      files.Get([[
          'https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345', '67890'
      ]], None).Validate()

  @mock.patch.object(files.file_util, 'CreateDirectories', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testUnzip(self, build_info, create_dir):
    src = '/tmp/input.zip'
    dst = '/out/dir/path'
    # bad args
    un = files.Unzip([], build_info)
    self.assertRaises(errors.ActionError, un.Run)
    un = files.Unzip([src], build_info)
    self.assertRaises(errors.ActionError, un.Run)
    # bad path
    un = files.Unzip([src, dst], build_info)
    self.assertRaises(errors.ActionError, un.Run)
    # create error
    create_dir.side_effect = errors.DirectoryCreationError('/some/dir/name')
    self.assertRaises(errors.ActionError, un.Run)
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
    self.assertRaises(errors.ValidationError, un.Validate)
    un = files.Unzip([1, 2, 3], None)
    self.assertRaises(errors.ValidationError, un.Validate)
    un = files.Unzip([1, '/tmp/out/path'], None)
    self.assertRaises(errors.ValidationError, un.Validate)
    un = files.Unzip(['/tmp/src.zip', 2], None)
    self.assertRaises(errors.ValidationError, un.Validate)
    un = files.Unzip(['/tmp/src.zip', '/tmp/out/path'], None)
    un.Validate()


if __name__ == '__main__':
  absltest.main()
