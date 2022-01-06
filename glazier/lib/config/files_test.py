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

from unittest import mock

from absl.testing import absltest
from glazier.lib import file_util
from glazier.lib.config import files
from pyfakefs import fake_filesystem


class FilesTest(absltest.TestCase):

  def setUp(self):
    super(FilesTest, self).setUp()
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
    self.filesystem.create_file('/tmp/downloaded1.yaml', contents='data: set1')
    self.filesystem.create_file('/tmp/downloaded2.yaml', contents='data: set2')
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

  @mock.patch.object(files.file_util, 'Remove', autospec=True)
  def testRemoveWithoutBackup(self, remove):
    files.Remove('/test/file/name.yaml', backup=False)
    remove.assert_called_with('/test/file/name.yaml')
    # error handling
    remove.side_effect = file_util.Error('test error')
    self.assertRaises(
        files.Error, files.Remove, '/test/file/name.yaml', backup=False)

  @mock.patch.object(files.file_util, 'Move', autospec=True)
  def testRemoveWithBackup(self, move):
    files.Remove('/test/file/name.yaml', backup=True)
    move.assert_called_with('/test/file/name.yaml', '/test/file/name.yaml.bak')
    # error handling
    move.side_effect = file_util.Error('test error')
    self.assertRaises(
        files.Error, files.Remove, '/test/file/name.yaml', backup=True)

  def testYamlReader(self):
    self.filesystem.create_file(
        '/foo/bar/baz.txt', contents='- item4\n- item5\n- item6')
    result = files._YamlReader('/foo/bar/baz.txt')
    self.assertEqual(result[1], 'item5')


if __name__ == '__main__':
  absltest.main()
