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

import os
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import buildinfo
from glazier.lib import cache
from glazier.lib import events
from glazier.lib import test_utils
from glazier.lib.actions import files


class FilesTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(FilesTest, self).setUp()
    files.WindowsError = Exception

  # TODO(b/152894756): Split into separate tests.
  @mock.patch.object(files.execute, 'execute_binary', autospec=True)
  @mock.patch.object(files.shlex, 'split', autospec=True)
  @mock.patch.object(files.cache.Cache, 'CacheFromLine', autospec=True)
  def test_execute(self, mock_cachefromline, mock_split, mock_execute_binary):
    bi = buildinfo.BuildInfo()
    mock_cachefromline.side_effect = iter(['cmd.exe /c', 'explorer.exe'])
    mock_execute_binary.return_value = 0
    e = files.Execute([['cmd.exe /c', [0]], ['explorer.exe']], bi)
    e.Run()
    self.assertTrue(mock_split.called)

    # success codes
    mock_cachefromline.side_effect = None
    mock_cachefromline.return_value = 'cmd.exe /c script.bat'
    e = files.Execute([['cmd.exe /c script.bat', [2, 4]]], bi)
    with self.assert_raises_with_validation(files.ActionError):
      e.Run()
    mock_execute_binary.return_value = 4
    e.Run()

    # reboot codes - no retry
    e = files.Execute([['cmd.exe /c script.bat', [0], [2, 4]]], bi)
    with self.assert_raises_with_validation(events.RestartEvent) as cm:
      e.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, False)

    # reboot codes -  retry
    e = files.Execute([['cmd.exe /c #script.bat', [0], [2, 4], True]], bi)
    with self.assert_raises_with_validation(events.RestartEvent) as cm:
      e.Run()
    exception = cm.exception
    self.assertEqual(exception.retry_on_restart, True)
    mock_cachefromline.assert_called_with(mock.ANY, 'cmd.exe /c #script.bat',
                                          bi)

    # Shell
    files.Execute([['cmd.exe /c #script.bat', [4], [0], True, True]], bi).Run()
    mock_execute_binary.assert_called_with(
        mock.ANY, mock.ANY, [4, 0], shell=True)

    # KeyboardInterrupt
    mock_execute_binary.side_effect = KeyboardInterrupt
    with self.assert_raises_with_validation(files.ActionError):
      e.Run()

    # Execute Error
    mock_execute_binary.side_effect = files.execute.ExecError('some_command')
    with self.assert_raises_with_validation(files.ActionError):
      e.Run()

    # ValueError
    mock_split.side_effect = ValueError
    with self.assert_raises_with_validation(files.ActionError):
      e.Run()

    # Cache error
    mock_cachefromline.side_effect = cache.CacheError('some/file/path')
    with self.assert_raises_with_validation(files.ActionError):
      e.Run()

  def test_execute_validation_success(self):
    e = files.Execute([['cmd.exe', [0], [2], False], ['explorer.exe']], None)
    e.Validate()

  @parameterized.named_parameters(
      ('_invalid_args_length', [[]], None),
      ('_expected_list_1', ['explorer.exe'], None),
      ('_expected_list_2', 'explorer.exe', None),
      ('_expected_list_3', [['cmd.exe', [0]], ['explorer.exe', '0']], None),
      ('_expected_int_1', [['cmd.exe', [0]], ['explorer.exe', ['0']]], None),
      ('_expected_int_2', [['cmd.exe', [0], ['2']], ['explorer.exe']], None),
      ('_expected_bool_1', [['cmd.exe', [0], [2], 'True'], ['explorer.exe']
                           ], None),
      ('_expected_bool_2', [['cmd.exe', [0], [2], False, 'True'],
                            ['explorer.exe']], None),
  )
  def test_execute_validation_failure(self, exec_args, build_info):
    e = files.Execute(exec_args, build_info)
    with self.assert_raises_with_validation(files.ValidationError):
      e.Validate()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_from_bin(self, mock_downloadfile, mock_branch, mock_binarypath,
                        mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    mock_binarypath.return_value = 'https://glazier-server.example.com/bin/'
    self.create_tempfile(
        file_path='autobuild.par.sha256',
        content='58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800'
    )
    mock_downloadfile.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    mock_downloadfile.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/bin/glazier/1.0/autobuild.par',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_from_conf(self, mock_downloadfile, mock_branch, mock_binarypath,
                         mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    mock_binarypath.return_value = 'https://glazier-server.example.com/bin/'
    mock_downloadfile.return_value = True
    files.Get([['#test/script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    mock_downloadfile.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/test/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_from_untagged(self, mock_downloadfile, mock_branch,
                             mock_binarypath, mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    mock_binarypath.return_value = 'https://glazier-server.example.com/bin/'
    mock_downloadfile.return_value = True
    files.Get([['test/script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    mock_downloadfile.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/test/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_from_local(self, mock_downloadfile, mock_branch, mock_binarypath,
                          mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'C:/glazier/conf'
    mock_binarypath.return_value = 'https://glazier-server.example.com/bin/'
    mock_downloadfile.return_value = True
    files.Get([['#script.ps1', '/tmp/autobuild.par']],
              buildinfo.BuildInfo()).Run()
    mock_downloadfile.assert_called_with(
        mock.ANY,
        'C:/glazier/conf/script.ps1',
        '/tmp/autobuild.par',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_download_err(self, mock_downloadfile, mock_branch,
                            mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    remote = '@glazier/1.0/autobuild.par'
    local = r'/tmp/autobuild.par'
    mock_downloadfile.side_effect = files.download.Error('Error')
    with self.assert_raises_with_validation(files.ActionError):
      files.Get([[remote, local]], buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_mkdir_err(self, mock_downloadfile, mock_branch,
                         mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    remote = '@glazier/1.0/autobuild.par'
    temp_dir = self.create_tempdir().full_path
    mock_downloadfile.side_effect = files.download.Error('Error')
    with self.assert_raises_with_validation(files.ActionError):
      temp_path = os.path.join(temp_dir, 'file.txt')
      files.Get([[remote, temp_path]], buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  def test_get_relative_path(self, mock_downloadfile, mock_branch,
                             mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    self.create_tempfile(
        file_path='autobuild.par.sha256',
        content='58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800'
    )
    mock_downloadfile.return_value = True
    files.Get([['autobuild.bat', '/tmp/autobuild.bat']],
              buildinfo.BuildInfo()).Run()
    mock_downloadfile.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/autobuild.bat',
        '/tmp/autobuild.bat',
        show_progress=True)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def test_get_hash_match(self, mock_verifyshahash, mock_downloadfile,
                          mock_branch, mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    local = r'/tmp/autobuild.par'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.create_tempfile(file_path='autobuild.par.sha256', content=test_sha256)
    mock_downloadfile.return_value = True
    mock_verifyshahash.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', local, test_sha256]],
              buildinfo.BuildInfo()).Run()
    mock_verifyshahash.assert_called_with(mock.ANY, local, test_sha256)

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def test_get_hash_mismatch(self, mock_verifyshahash, mock_downloadfile,
                             mock_branch, mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800')
    self.create_tempfile(file_path='autobuild.par.sha256', content=test_sha256)
    mock_downloadfile.return_value = True
    mock_verifyshahash.return_value = False
    with self.assert_raises_with_validation(files.ActionError):
      files.Get(
          [['@glazier/1.0/autobuild.par', r'/tmp/autobuild.par', test_sha256]],
          buildinfo.BuildInfo()).Run()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(files.download.Download, 'DownloadFile', autospec=True)
  @mock.patch.object(files.download.Download, 'VerifyShaHash', autospec=True)
  def test_get_no_hash(self, mock_verifyshahash, mock_downloadfile, mock_branch,
                       mock_releasepath):
    mock_branch.return_value = 'stable'
    mock_releasepath.return_value = 'https://glazier-server.example.com/'
    self.create_tempfile(
        file_path='autobuild.par.sha256',
        content='58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae800'
    )
    mock_downloadfile.return_value = True
    files.Get([['@glazier/1.0/autobuild.par', r'/tmp/autobuild.par', '']],
              buildinfo.BuildInfo()).Run()
    self.assertFalse(mock_verifyshahash.called)

  def test_get_validate(self):
    with self.assert_raises_with_validation(files.ValidationError):
      files.Get('String', None).Validate()
    with self.assert_raises_with_validation(files.ValidationError):
      files.Get([[1, 2, 3]], None).Validate()
    with self.assert_raises_with_validation(files.ValidationError):
      files.Get([[1, '/tmp/out/path']], None).Validate()
    with self.assert_raises_with_validation(files.ValidationError):
      files.Get([['/tmp/src.zip', 2]], None).Validate()
    files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip']],
              None).Validate()
    files.Get([['https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345']],
              None).Validate()
    with self.assert_raises_with_validation(files.ValidationError):
      files.Get([[
          'https://glazier/bin/src.zip', '/tmp/out/src.zip', '12345', '67890'
      ]], None).Validate()

  @mock.patch.object(files.file_util, 'CreateDirectories', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_unzip(self, mock_buildinfo, mock_createdirectories):

    src = '/tmp/input.zip'
    dst = '/out/dir/path'

    # bad args
    un = files.Unzip([], mock_buildinfo)
    with self.assert_raises_with_validation(files.ActionError):
      un.Run()
    un = files.Unzip([src], mock_buildinfo)
    with self.assert_raises_with_validation(files.ActionError):
      un.Run()

    # bad path
    un = files.Unzip([src, dst], mock_buildinfo)
    with self.assert_raises_with_validation(files.ActionError):
      un.Run()

    # create error
    mock_createdirectories.side_effect = files.file_util.DirectoryCreationError(
        'some_dir')
    with self.assert_raises_with_validation(files.ActionError):
      un.Run()

    # good
    mock_createdirectories.side_effect = None
    with mock.patch.object(files.zipfile, 'ZipFile', autospec=True) as z:
      un = files.Unzip([src, dst], mock_buildinfo)
      un.Run()
      z.assert_called_with(src)
      z.return_value.extractall.assert_called_with(dst)
      mock_createdirectories.assert_called_with(dst)

  def test_unzip_validate(self):
    un = files.Unzip('String', None)
    with self.assert_raises_with_validation(files.ValidationError):
      un.Validate()
    un = files.Unzip([1, 2, 3], None)
    with self.assert_raises_with_validation(files.ValidationError):
      un.Validate()
    un = files.Unzip([1, '/tmp/out/path'], None)
    with self.assert_raises_with_validation(files.ValidationError):
      un.Validate()
    un = files.Unzip(['/tmp/src.zip', 2], None)
    with self.assert_raises_with_validation(files.ValidationError):
      un.Validate()
    un = files.Unzip(['/tmp/src.zip', '/tmp/out/path'], None)
    un.Validate()


if __name__ == '__main__':
  absltest.main()
