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

import io
from unittest import mock

from absl import flags
from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import beyondcorp
from glazier.lib import buildinfo
from glazier.lib import download
from glazier.lib import file_util
from glazier.lib import test_utils

_TEST_INI = """
[BUILD]
release=1.0
branch=stable
"""

FLAGS = flags.FLAGS
SLEEP = 20
_TEST_URI = 'https://www.example.com'
_TEST_URI_YAML = f'{_TEST_URI}/build.yaml'
_CONFIG_SERVER = _TEST_URI
_BINARY_SERVER = f'{_TEST_URI}/bin'


class HelperTests(test_utils.GlazierTestCase):

  def test_is_remote(self):
    self.assertTrue(download.IsRemote('http://glazier.example.com'))
    self.assertTrue(download.IsRemote('https://glazier.example.com'))
    self.assertTrue(download.IsRemote('HTTPS://glazier.example.com'))
    self.assertFalse(download.IsRemote('String with HTTP in it.'))
    self.assertFalse(download.IsRemote('C:/glazier'))

  def test_is_local(self):
    self.assertTrue(download.IsLocal('C:/glazier'))
    self.assertTrue(download.IsLocal(r'C:\glazier'))
    self.assertFalse(download.IsLocal('http://glazier.example.com'))
    self.assertFalse(download.IsLocal(r'String with C:\glazier in it.'))


class PathsTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(PathsTest, self).setUp()
    self.buildinfo = buildinfo.BuildInfo()

  @mock.patch.object(buildinfo.BuildInfo, 'ReleasePath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'BinaryPath', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def test_transform(self, mock_branch, mock_binarypath, mock_releasepath):
    mock_releasepath.return_value = 'https://glazier'
    mock_binarypath.return_value = 'https://glazier/bin/'
    mock_branch.return_value = 'stable'

    # Test '#' replacement
    result = download.Transform(r'#\#My-Script.ps1', self.buildinfo)
    self.assertEqual(result, r'https://glazier/#My-Script.ps1')

    # Test '@' replacement
    result = download.Transform(r'@install/\@1.0.0/installer.exe',
                                self.buildinfo)
    self.assertEqual(result, 'https://glazier/bin/install/@1.0.0/installer.exe')

    # Test '%' replacement
    result = download.Transform(
        r'@path/to/binary/%/\%googlechromestandaloneenterprise64.msi',
        self.buildinfo)
    self.assertEqual(
        result,
        r'https://glazier/bin/path/to/binary/stable/%googlechromestandaloneenterprise64.msi'
    )

    result = download.Transform('nothing _ here', self.buildinfo)
    self.assertEqual(result, 'nothing _ here')

  def test_path_compile(self):
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


class DownloadTest(test_utils.GlazierTestCase):

  def patch_constant(self, module, constant_name, new_value):
    patcher = mock.patch.object(module, constant_name, new_value)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def failing_url_open(self, *unused_args, **unused_kwargs):
    raise download.urllib.error.HTTPError('Error', None, None, None, None)

  def setUp(self):

    super(DownloadTest, self).setUp()
    self._dl = download.BaseDownloader()

    self.input_ini_path = self.create_tempfile(
        file_path='input.ini', content=_TEST_INI)

    # Very important, unless you want tests that fail indefinitely to backoff
    # for 10 minutes.
    self.patch_constant(download, 'BACKOFF_MAX_TIME', 20)  # in seconds

  def test_convert_bytes(self):
    self.assertEqual(self._dl._ConvertBytes(123), '123.00B')
    self.assertEqual(self._dl._ConvertBytes(23455), '22.91KB')
    self.assertEqual(self._dl._ConvertBytes(3455555), '3.30MB')
    self.assertEqual(self._dl._ConvertBytes(456555555), '435.41MB')
    self.assertEqual(self._dl._ConvertBytes(56755555555), '52.86GB')
    self.assertEqual(self._dl._ConvertBytes(6785555555555), '6.17TB')

  @mock.patch.object(download.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(download.urllib.request, 'urlopen', autospec=True)
  def test_open_stream_internal(self, mock_urlopen, mock_check_winpe):

    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    url = _TEST_URI_YAML
    httperr = download.urllib.error.HTTPError('Error', None, None, None, None)
    urlerr = download.urllib.error.URLError('Error')
    mock_check_winpe.return_value = False

    # 200
    mock_urlopen.side_effect = iter([httperr, urlerr, file_stream])
    res = self._dl._OpenStream(url)
    self.assertEqual(res, file_stream)

    # Invalid URL
    with self.assertRaisesRegex(download.Error, 'Invalid remote server URL*'):
      self._dl._OpenStream('not_a_real_url')

    # 404
    file_stream.getcode.return_value = 404
    mock_urlopen.side_effect = iter([httperr, file_stream])
    with self.assert_raises_with_validation(download.Error):
      self._dl._OpenStream(url)

  @mock.patch.object(download.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(download.urllib.request, 'urlopen', autospec=True)
  def test_open_file_stream_gives_up(self, mock_urlopen, mock_check_winpe):

    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    mock_check_winpe.return_value = False

    mock_urlopen.side_effect = self.failing_url_open
    with self.assert_raises_with_validation(download.Error):
      self._dl._OpenStream(_TEST_URI_YAML)

  @mock.patch.object(download.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(download.urllib.request, 'urlopen', autospec=True)
  def test_check_url(self, mock_urlopen, mock_check_winpe):
    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    mock_check_winpe.return_value = False

    # match
    mock_urlopen.side_effect = iter([file_stream])
    self.assertTrue(self._dl.CheckUrl(_TEST_URI_YAML, status_codes=[200]))
    # miss
    mock_urlopen.side_effect = iter([file_stream])
    self.assertFalse(self._dl.CheckUrl(_TEST_URI_YAML, status_codes=[201]))

  @mock.patch.object(file_util, 'Copy', autospec=True)
  def test_download_file_local(self, mock_copy):
    self._dl.DownloadFile(
        url='c:/glazier/conf/test.ps1', save_location='c:/windows/test.ps1')
    mock_copy.assert_called_with('c:/glazier/conf/test.ps1',
                                 'c:/windows/test.ps1')

  @mock.patch.object(file_util, 'Copy', autospec=True)
  def test_download_file_copy_except(self, mock_copy):
    mock_copy.side_effect = file_util.Error('copy error')
    with self.assert_raises_with_validation(download.Error):
      self._dl.DownloadFile(
          url='c:/glazier/conf/test.ps1', save_location='c:/windows/test.ps1')

  @mock.patch.object(download.BaseDownloader, '_StreamToDisk', autospec=True)
  @mock.patch.object(download.BaseDownloader, '_OpenStream', autospec=True)
  @mock.patch.object(download.tempfile, 'NamedTemporaryFile', autospec=True)
  @mock.patch.object(beyondcorp.BeyondCorp, 'CheckBeyondCorp', autospec=True)
  def test_download_file_temp(self, mock_checkbeyondcorp,
                              mock_namedtemporaryfile, mock_openstream,
                              mock_streamtodisk):

    mock_checkbeyondcorp.return_value = False
    url = _TEST_URI_YAML
    path = r'C:\Windows\Temp\tmpblahblah'
    mock_namedtemporaryfile.return_value.name = path
    self._dl.DownloadFileTemp(url)
    mock_openstream.assert_called_with(self._dl, url)
    mock_streamtodisk.assert_called_with(self._dl, mock_openstream.return_value,
                                         False)
    self.assertEqual(self._dl._save_location, path)
    self._dl.DownloadFileTemp(url, show_progress=True)
    mock_openstream.assert_called_with(self._dl, url)
    mock_streamtodisk.assert_called_with(self._dl, mock_openstream.return_value,
                                         True)
    self._dl.DownloadFileTemp(url, show_progress=False)
    mock_openstream.assert_called_with(self._dl, url)
    mock_streamtodisk.assert_called_with(self._dl, mock_openstream.return_value,
                                         False)

  @parameterized.named_parameters(
      ('standard_binary_server', True, _BINARY_SERVER, ''),
      ('standard_config_server', True, '', _CONFIG_SERVER),
      ('standard_neither', True, '', ''),
      ('standard_both', True, _BINARY_SERVER, _CONFIG_SERVER),
      ('beyond_corp_binary_server', True, _BINARY_SERVER, ''),
      ('beyond_corp_config_server', True, '', _CONFIG_SERVER),
      ('beyond_corp_neither', True, '', ''),
      ('beyond_corp_both', True, _BINARY_SERVER, _CONFIG_SERVER),
  )
  @mock.patch.object(beyondcorp.BeyondCorp, 'GetSignedUrl', autospec=True)
  def test_set_url(self, use_signed_url, binary_server, config_server,
                   mock_get_signed_url):
    FLAGS.use_signed_url = use_signed_url
    FLAGS.binary_server = binary_server
    FLAGS.config_server = config_server
    uri = _TEST_URI_YAML
    if not FLAGS.use_signed_url:
      self.assertFalse(mock_get_signed_url.called)
      self.assertEqual(self._dl._SetUrl(uri), uri)
      return

    self._dl._SetUrl(uri)
    if uri.startswith(FLAGS.binary_server):
      uri = uri.replace(f'{FLAGS.binary_server}/', '')
    if uri.startswith(FLAGS.config_server):
      uri = uri.replace(f'{FLAGS.config_server}/', '')
    mock_get_signed_url.assert_called_with(mock.ANY, uri)

  @mock.patch.object(beyondcorp.BeyondCorp, 'GetSignedUrl', autospec=True)
  def test_set_url_error(self, mock_get_signed_url):
    FLAGS.use_signed_url = True
    mock_get_signed_url.side_effect = beyondcorp.Error
    with self.assertRaises(download.SignedUrlError):
      self._dl._SetUrl(_TEST_URI_YAML)
    self.assertTrue(mock_get_signed_url.called)

  @mock.patch.object(download.BaseDownloader, '_StoreDebugInfo', autospec=True)
  def test_stream_to_disk(self, mock_storedebuginfo):

    # setup
    http_stream = io.BytesIO()
    http_stream.write(b'First line.\nSecond line.\n')
    http_stream.seek(0)
    download.CHUNK_BYTE_SIZE = 5
    file_stream = mock.Mock()
    file_stream.getcode.return_value = 200
    file_stream.geturl.return_value = _TEST_URI_YAML
    file_stream.headers.get = lambda x: {'Content-Length': '25'}[x]
    file_stream.read = http_stream.read

    # success
    self._dl._save_location = self.create_tempfile(file_path='download.txt')
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
      with self.assert_raises_with_validation(download.Error):
        self._dl._StreamToDisk(None)

    # IOError
    http_stream.seek(0)
    temp_dir = self.create_tempdir()
    self._dl._save_location = temp_dir
    with self.assert_raises_with_validation(download.Error):
      self._dl._StreamToDisk(file_stream)

    # File Size
    http_stream.seek(0)
    file_stream.headers.get = lambda x: {'Content-Length': '100000'}[x]
    self._dl._save_location = self.create_tempfile(file_path='download.txt')
    with self.assert_raises_with_validation(download.Error):
      self._dl._StreamToDisk(file_stream)

    # Socket Error
    http_stream.seek(0)
    file_stream.headers.get = lambda x: {'Content-Length': '25'}[x]
    file_stream.read = mock.Mock(side_effect=download.socket.error('SocketErr'))
    with self.assert_raises_with_validation(download.Error):
      self._dl._StreamToDisk(file_stream)
    mock_storedebuginfo.assert_called_with(self._dl, file_stream, 'SocketErr')

    # Retries
    http_stream.seek(0)
    file_stream.headers.get = lambda x: {'Content-Length': '100000'}[x]
    self._dl._save_location = self.create_tempfile(file_path='download.txt')
    with self.assert_raises_with_validation(download.Error):
      self._dl._StreamToDisk(file_stream)

  @mock.patch.object(download.BaseDownloader, '_StoreDebugInfo', autospec=True)
  def test_validate(self, mock_storedebuginfo):
    file_stream = mock.Mock()
    self._dl._save_location = r'C:\missing.txt'
    with self.assert_raises_with_validation(download.Error):
      self._dl._Validate(file_stream, 200)
    mock_storedebuginfo.assert_called_with(self._dl, file_stream)

  def test_verify_sha_hash(self):
    test_sha256 = (
        '58157BF41CE54731C0577F801035D47EC20ED16A954F10C29359B8ADEDCAE800')
    # sha256
    result = self._dl.VerifyShaHash(self.input_ini_path, test_sha256)
    self.assertTrue(result)
    # missing source
    result = self._dl.VerifyShaHash(r'C:\missing.ini', test_sha256)
    self.assertFalse(result)
    # missing hash
    result = self._dl.VerifyShaHash(self.input_ini_path, '')
    self.assertFalse(result)
    # mismatch hash
    test_sha256 = (
        '58157bf41ce54731c0577f801035d47ec20ed16a954f10c29359b8adedcae801')
    result = self._dl.VerifyShaHash(self.input_ini_path, test_sha256)
    self.assertFalse(result)


if __name__ == '__main__':
  absltest.main()
