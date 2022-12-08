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

"""Tests for glazier.lib.cache."""

import os
from unittest import mock

from absl.testing import absltest
from glazier.lib import cache
from glazier.lib import test_utils


class CacheTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(CacheTest, self).setUp()
    self.cache = cache.Cache()

  def fake_transform(self, string, unused_info):
    if '#' in string:
      string = string.replace('#', 'https://test.example.com/release/')
    if '@' in string:
      string = string.replace('@', 'https://test.example.com/bin/')
    return string

  @mock.patch.object(cache.download, 'Transform', autospec=True)
  @mock.patch.object(cache.download.Download, 'DownloadFile', autospec=True)
  def test_cache_from_line(self, mock_downloadfile, mock_transform):
    cache_path = r'C:\Cache\Path'
    build_info = mock.Mock()
    build_info.CachePath.return_value = cache_path
    remote1 = r'folder/other/installer.msi'
    remote2 = r'config_file.conf'
    local1 = os.path.join(cache_path, 'installer.msi')
    local2 = os.path.join(cache_path, 'config_file.conf')
    line_in = 'msiexec /i @%s /qa /l*v CONF=#%s' % (remote1, remote2)
    line_out = 'msiexec /i %s /qa /l*v CONF=%s' % (local1, local2)
    mock_downloadfile.return_value = True
    mock_transform.side_effect = self.fake_transform
    result = self.cache.CacheFromLine(line_in, build_info)
    self.assertEqual(result, line_out)
    call1 = mock.call(self.cache._downloader,
                      'https://test.example.com/bin/%s' % remote1, local1)
    call2 = mock.call(self.cache._downloader,
                      'https://test.example.com/release/%s' % remote2, local2)
    mock_downloadfile.assert_has_calls([call1, call2])
    # download exception
    transfer_err = cache.download.Error('Error message.')
    mock_downloadfile.side_effect = transfer_err
    with self.assert_raises_with_validation(cache.CacheError):
      self.cache.CacheFromLine('@%s' % remote2, build_info)

  @mock.patch.object(cache.download, 'Transform', autospec=True)
  def test_cache_from_line_local(self, mock_transform):
    line_in = 'powershell.exe -file @path/to/script.ps1'
    line_out = 'powershell.exe -file C:/glazier/path/to/script.ps1'
    mock_transform.return_value = 'C:/glazier/path/to/script.ps1'
    result = self.cache.CacheFromLine(line_in, mock.Mock())
    self.assertEqual(result, line_out)

  def test_destination_path(self):
    path = self.cache._DestinationPath(
        'C:', 'http://some.web.address/folder/other/'
        'an_installer.msi')
    self.assertEqual(path, os.path.join('C:', 'an_installer.msi'))

  def test_find_download(self):
    line_test = self.cache._FindDownload('powershell -file '
                                         r'C:\run_some_file.ps1')
    self.assertIsNone(line_test)
    line_test = self.cache._FindDownload('msiexec /i @installer.msi /qa')
    self.assertEqual(line_test, '@installer.msi')
    line_test = self.cache._FindDownload(r'C:\install_some_program.exe '
                                         '/i ARGS=FOO')
    self.assertIsNone(line_test)
    line_test = self.cache._FindDownload(
        'some_executable.exe /conf=#remote.conf /flag1 /flag1')
    self.assertEqual(line_test, '#remote.conf')


if __name__ == '__main__':
  absltest.main()
