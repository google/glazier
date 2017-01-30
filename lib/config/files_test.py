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

"""Tests for glazier.lib.config.files."""

from pyfakefs import fake_filesystem
from glazier.lib.config import files
import mock
from google.apputils import basetest


class FilesTest(basetest.TestCase):

  def setUp(self):
    self.filesystem = fake_filesystem.FakeFilesystem()
    files.open = fake_filesystem.FakeFileOpen(self.filesystem)
    files.file_util.os = fake_filesystem.FakeOsModule(self.filesystem)

  def testDump(self):
    op_list = ['op1', ['op2a', 'op2b'], 'op3', {'op4a': 'op4b'}]
    files.Dump('/tmp/foo/dump.txt', op_list)
    result = files._YamlReader('/tmp/foo/dump.txt')
    self.assertEqual(result[1], ['op2a', 'op2b'])
    self.assertEqual(result[3], {'op4a': 'op4b'})
    self.assertRaises(files.Error, files.Dump, '/tmp', [])

  @mock.patch.object(files.download.Download, 'DownloadFileTemp', autospec=True)
  def testRead(self, download):
    self.filesystem.CreateFile('/tmp/downloaded1.yaml', contents='data: set1')
    self.filesystem.CreateFile('/tmp/downloaded2.yaml', contents='data: set2')
    download.return_value = '/tmp/downloaded1.yaml'
    result = files.Read(
        'https://glazier-server.example.com/unstable/dir/test-build.yaml')
    download.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/unstable/dir/test-build.yaml')
    self.assertEqual(result['data'], 'set1')
    # download error
    download.side_effect = files.download.DownloadError
    self.assertRaises(
        files.Error, files.Read,
        'https://glazier-server.example.com/unstable/dir/test-build.yaml')
    # local
    result = files.Read('/tmp/downloaded2.yaml')
    self.assertEqual(result['data'], 'set2')

  def testYamlReader(self):
    self.filesystem.CreateFile(
        '/foo/bar/baz.txt', contents='- item4\n- item5\n- item6')
    result = files._YamlReader('/foo/bar/baz.txt')
    self.assertEqual(result[1], 'item5')


if __name__ == '__main__':
  basetest.main()
