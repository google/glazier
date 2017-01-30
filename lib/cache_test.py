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
from pyfakefs import fake_filesystem
from glazier.lib import cache
import mock
from google.apputils import basetest


class CacheTest(basetest.TestCase):

  def setUp(self):
    self.cache = cache.Cache()
    fs = fake_filesystem.FakeFilesystem()
    fs.CreateDirectory(r'C:\Directory')
    os_module = fake_filesystem.FakeOsModule(fs)
    self.mock_open = fake_filesystem.FakeFileOpen(fs)
    cache.os = os_module
    cache.open = self.mock_open

  def MockTransform(self, string, unused_info):
    if '#' in string:
      string = string.replace('#', 'https://test.example.com/release/')
    if '@' in string:
      string = string.replace('@', 'https://test.example.com/bin/')
    return string

  @mock.patch.object(cache.download, 'Transform', autospec=True)
  @mock.patch.object(cache.download.Download, 'DownloadFile', autospec=True)
  def testCacheFromLine(self, download, transform):
    remote1 = r'folder/other/installer.msi'
    remote2 = r'config_file.conf'
    local1 = os.path.join(self.cache.Path(), 'installer.msi')
    local2 = os.path.join(self.cache.Path(), 'config_file.conf')
    line_in = 'msiexec /i @%s /qa /l*v CONF=#%s' % (remote1, remote2)
    line_out = 'msiexec /i %s /qa /l*v CONF=%s' % (local1, local2)
    download.return_value = True
    transform.side_effect = self.MockTransform
    result = self.cache.CacheFromLine(line_in, None)
    self.assertEqual(result, line_out)
    call1 = mock.call(self.cache._downloader,
                      'https://test.example.com/bin/%s' % remote1, local1)
    call2 = mock.call(self.cache._downloader,
                      'https://test.example.com/release/%s' % remote2, local2)
    download.assert_has_calls([call1, call2])
    # download exception
    transfer_err = cache.download.DownloadError('Error message.')
    download.side_effect = transfer_err
    self.assertRaises(cache.CacheError, self.cache.CacheFromLine,
                      '@%s' % remote2, None)

  def testDestinationPath(self):
    path = self.cache._DestinationPath('http://some.web.address/folder/other/'
                                       'an_installer.msi')
    self.assertEqual(path, os.path.join(self.cache.Path(), 'an_installer.msi'))

  def testFindDownload(self):
    line_test = self.cache._FindDownload('powershell -file '
                                         r'C:\run_some_file.ps1')
    self.assertEqual(line_test, None)
    line_test = self.cache._FindDownload('msiexec /i @installer.msi /qa')
    self.assertEqual(line_test, '@installer.msi')
    line_test = self.cache._FindDownload(r'C:\install_some_program.exe '
                                         '/i ARGS=FOO')
    self.assertEqual(line_test, None)
    line_test = self.cache._FindDownload(
        'some_executable.exe /conf=#remote.conf /flag1 /flag1')
    self.assertEqual(line_test, '#remote.conf')


if __name__ == '__main__':
  basetest.main()
