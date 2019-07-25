# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for glazier.lib.download."""

from absl.testing import absltest
from absl.testing import flagsaver
from pyfakefs import fake_filesystem
from glazier.lib import buildinfo
from glazier.lib import download

import mock
import six


_TEST_INI = """
[BUILD]
release=1.0
branch=stable
"""


class PathsTest(absltest.TestCase):

  def setUp(self):
    super(PathsTest, self).setUp()
    self.buildinfo = buildinfo.BuildInfo()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  def testTransform(self, binpath, relpath):
    # pylint: disable=line-too-long
    # common_typos_disable
    relpath.return_value = 'https://glazier'
    binpath.return_value = 'https://glazier/bin/'

    result = download.Transform(r'sccm.x86_64.1.00.1337\#13371337.exe',
                                self.buildinfo)
    self.assertEqual(result, 'sccm.x86_64.1.00.1337#13371337.exe')

    result = download.Transform(r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -File #My-Script.ps1 -Verbose', self.buildinfo)
    self.assertEqual(result, r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -File https://glazier/My-Script.ps1 -Verbose')

    result = download.Transform(r'@Corp/install/1.0.0/installer.exe sccm.x86_64.1.00.1337\@13371337.exe',
                                self.buildinfo)
    self.assertEqual(result, 'https://glazier/bin/Corp/install/1.0.0/installer.exe sccm.x86_64.1.00.1337@13371337.exe')

    result = download.Transform(r'C:\Windows\System32\msiexec.exe /i @Google/Chrome/1.3.3.7/googlechromestandaloneenterprise64.msi /qb /norestart', self.buildinfo)
    self.assertEqual(result, r'C:\Windows\System32\msiexec.exe /i https://glazier/bin/Google/Chrome/1.3.3.7/googlechromestandaloneenterprise64.msi /qb /norestart')

    result = download.Transform('nothing _ here', self.buildinfo)
    self.assertEqual(result, 'nothing _ here')

  def testPathCompile(self):
    result = download.PathCompile(
        self.buildinfo, file_name='file.txt', base='/tmp/base')
    self.assertEqual(result, '/tmp/base/file.txt')
    self.buildinfo._active_conf_path = ['sub', 'dir']
    result = download.PathCompile(
        self.buildinfo, file_name='/file.txt', base='/tmp/base')
    self.assertEqual(result, '/tmp/base/sub/dir/file.txt')
    result = download.PathCompile(
        self.buildinfo, file_name='file.txt', base='/tmp/base')
    self.assertEqual(result, '/tmp/base/sub/dir/file.txt')
    self.buildinfo._active_conf_path = ['sub', 'dir/other', 'another/']
    result = download.PathCompile(
        self.buildinfo, file_name='/file.txt', base='/tmp/')
    self.assertEqual(result, '/tmp/sub/dir/other/another/file.txt')


class DownloadTest(absltest.TestCase):

  def setUp(self):
    super(DownloadTest, self).setUp()
    self._dl = download.BaseDownloader()
    # filesystem
    self.filesystem = fake_filesystem.FakeFilesystem()
    self.filesystem.CreateFile(r'C:\input.ini', contents=_TEST_INI)
    download.os = fake_filesystem.FakeOsModule(self.filesystem)
    download.open = fake_filesystem.FakeFileOpen(self.filesystem)

  def testConvertBytes(self):
    self.assertEqual(self._dl._ConvertBytes(123), '123.00B')
    self.assertEqual(self._dl._ConvertBytes(23455), '22.91KB')
    self.assertEqual(self._dl._ConvertBytes(3455555), '3.30MB')
    self.assertEqual(self._dl._ConvertBytes(456555555), '435.41MB')
    self.assertEqual(self._dl._ConvertBytes(56755555555), '52.86GB')
    self.assertEqual(self._dl._ConvertBytes(6785555555555), '6.17TB')

  @mock.patch.object(download.urllib.request, 'urlopen', autospec=True)
  @mock.patch.object(download.time, 'sleep', autospec=True)
  def testOpenStreamInternal(self, sleep, urlopen):
    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    httperr = download.urllib.error.HTTPError('Error', None, None, None, None)
    urlerr = download.urllib.error.URLError('Error')
    # 200
    urlopen.side_effect = iter([httperr, urlerr, file_stream])
    res = self._dl._OpenStream(
        'https://www.example.com/build.yaml', max_retries=4)
    self.assertEqual(res, file_stream)
    # 404
    file_stream.getcode.return_value = 404
    urlopen.side_effect = iter([httperr, file_stream])
    self.assertRaises(download.DownloadError, self._dl._OpenStream,
                      'https://www.example.com/build.yaml')
    # retries
    file_stream.getcode.return_value = 200
    urlopen.side_effect = iter([httperr, httperr, file_stream])
    self.assertRaises(
        download.DownloadError,
        self._dl._OpenStream,
        'https://www.example.com/build.yaml',
        max_retries=2)
    sleep.assert_has_calls([mock.call(20), mock.call(20)])

  @mock.patch.object(download.urllib.request, 'urlopen', autospec=True)
  def testCheckUrl(self, urlopen):
    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    # match
    urlopen.side_effect = iter([file_stream])
    self.assertTrue(
        self._dl.CheckUrl(
            'https://www.example.com/build.yaml', status_codes=[200]))
    # miss
    urlopen.side_effect = iter([file_stream])
    self.assertFalse(
        self._dl.CheckUrl(
            'https://www.example.com/build.yaml',
            max_retries=1,
            status_codes=[201]))

  @mock.patch.object(download.BaseDownloader, '_StreamToDisk', autospec=True)
  @mock.patch.object(download.BaseDownloader, '_OpenStream', autospec=True)
  @mock.patch.object(download.tempfile, 'NamedTemporaryFile', autospec=True)
  def testDownloadFileTemp(self, tempf, downf, todisk):
    url = 'https://www.example.com/build.yaml'
    path = r'C:\Windows\Temp\tmpblahblah'
    tempf.return_value.name = path
    self._dl.DownloadFileTemp(url, max_retries=5)
    downf.assert_called_with(self._dl, url, 5)
    todisk.assert_called_with(self._dl, downf.return_value, False)
    self.assertEqual(self._dl._save_location, path)
    self._dl.DownloadFileTemp(url, max_retries=5, show_progress=True)
    downf.assert_called_with(self._dl, url, 5)
    todisk.assert_called_with(self._dl, downf.return_value, True)
    self._dl.DownloadFileTemp(url, max_retries=5, show_progress=False)
    downf.assert_called_with(self._dl, url, 5)
    todisk.assert_called_with(self._dl, downf.return_value, False)

  @mock.patch.object(download.BaseDownloader, '_StoreDebugInfo', autospec=True)
  def testStreamToDisk(self, store_info):
    # setup
    http_stream = six.BytesIO()
    http_stream.write(b'First line.\nSecond line.\n')
    http_stream.seek(0)
    download.CHUNK_BYTE_SIZE = 5
    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    file_stream.geturl.return_value = 'https://www.example.com/build.yaml'
    file_stream.info.return_value.getheader.return_value = '25'
    file_stream.read = http_stream.read
    # success
    self._dl._save_location = r'C:\download.txt'
    self._dl._StreamToDisk(file_stream)
    # Progress
    with mock.patch.object(
        self._dl, '_DownloadChunkReport', autospec=True) as report:
      # default false
      self._dl._default_show_progress = False
      http_stream.seek(0)
      self._dl._StreamToDisk(file_stream)
      self.assertFalse(report.called)
      # override true
      http_stream.seek(0)
      report.reset_mock()
      self._dl._StreamToDisk(file_stream, show_progress=True)
      self.assertTrue(report.called)
      # default true
      self._dl._default_show_progress = True
      http_stream.seek(0)
      report.reset_mock()
      self._dl._StreamToDisk(file_stream)
      self.assertTrue(report.called)
      # override false
      http_stream.seek(0)
      report.reset_mock()
      self._dl._StreamToDisk(file_stream, show_progress=False)
      self.assertFalse(report.called)
      # HTTP Header returned nothing (NoneType)
      http_stream.seek(0)
      report.reset_mock()
      self.assertRaises(download.DownloadError, self._dl._StreamToDisk,
                        None)
    # IOError
    http_stream.seek(0)
    self.filesystem.CreateDirectory(r'C:\Windows')
    self._dl._save_location = r'C:\Windows'
    self.assertRaises(download.DownloadError, self._dl._StreamToDisk,
                      file_stream)
    # File Size
    http_stream.seek(0)
    file_stream.info.return_value.getheader.return_value = '100000'
    self._dl._save_location = r'C:\download.txt'
    self.assertRaises(download.DownloadError, self._dl._StreamToDisk,
                      file_stream)
    # Socket Error
    http_stream.seek(0)
    file_stream.info.return_value.getheader.return_value = '25'
    file_stream.read = mock.Mock(side_effect=download.socket.error('SocketErr'))
    self.assertRaises(download.DownloadError, self._dl._StreamToDisk,
                      file_stream)
    store_info.assert_called_with(self._dl, file_stream, 'SocketErr')

  @mock.patch.object(download.BaseDownloader, '_StoreDebugInfo', autospec=True)
  def testValidate(self, store_info):
    file_stream = mock.Mock()
    self._dl._save_location = r'C:\missing.txt'
    self.assertRaises(download.DownloadError, self._dl._Validate, file_stream,
                      200)
    store_info.assert_called_with(self._dl, file_stream)

  def testVerifyShaHash(self):
    test_sha256 = (
        '58157BF41CE54731C0577F801035D47EC20ED16A954F10C29359B8ADEDCAE800')
    # sha256
    result = self._dl.VerifyShaHash(r'C:\input.ini', test_sha256)
    self.assertTrue(result)
    # missing source
    result = self._dl.VerifyShaHash(r'C:\missing.ini', test_sha256)
    self.assertFalse(result)
    # missing hash
    result = self._dl.VerifyShaHash(r'C:\input.ini', '')
    self.assertFalse(result)
    # mismatch hash
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae801')
    result = self._dl.VerifyShaHash(r'C:\input.ini', test_sha256)
    self.assertFalse(result)



if __name__ == '__main__':
  absltest.main()
