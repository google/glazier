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
from glazier.lib import test_utils
from glazier.lib.config import files


class FilesTest(test_utils.GlazierTestCase):

  def test_dump(self):
    op_list = ['op1', ['op2a', 'op2b'], 'op3', {'op4a': 'op4b'}]
    files.Dump('/tmp/foo/dump.txt', op_list)
    result = files._YamlReader('/tmp/foo/dump.txt')
    self.assertEqual(result[1], ['op2a', 'op2b'])
    self.assertEqual(result[3], {'op4a': 'op4b'})
    with self.assert_raises_with_validation(files.Error):
      files.Dump('/tmp', [])

  @mock.patch.object(files.download.Download, 'DownloadFileTemp', autospec=True)
  def test_read(self, mock_downloadtempfile):

    temp_file_1 = self.create_tempfile(
        file_path='downloaded1.yaml', content='data: set1').full_path
    temp_file_2 = self.create_tempfile(
        file_path='downloaded2.yaml', content='data: set2').full_path
    mock_downloadtempfile.return_value = temp_file_1

    result = files.Read(
        'https://glazier-server.example.com/unstable/dir/test-build.yaml')
    mock_downloadtempfile.assert_called_with(
        mock.ANY,
        'https://glazier-server.example.com/unstable/dir/test-build.yaml')
    self.assertEqual(result['data'], 'set1')

    # download error
    mock_downloadtempfile.side_effect = files.download.MissingFileStreamError()
    with self.assert_raises_with_validation(files.Error):
      files.Read(
          'https://glazier-server.example.com/unstable/dir/test-build.yaml')

    # local
    result = files.Read(temp_file_2)
    self.assertEqual(result['data'], 'set2')

  @mock.patch.object(files.file_util, 'Remove', autospec=True)
  def test_remove_without_backup(self, mock_remove):

    files.Remove('/test/file/name.yaml', backup=False)
    mock_remove.assert_called_with('/test/file/name.yaml')

    # error handling
    mock_remove.side_effect = file_util.Error('test error')
    with self.assert_raises_with_validation(files.Error):
      files.Remove('/test/file/name.yaml', backup=False)

  @mock.patch.object(files.file_util, 'Move', autospec=True)
  def test_remove_with_backup(self, mock_move):

    files.Remove('/test/file/name.yaml', backup=True)
    mock_move.assert_called_with(
        '/test/file/name.yaml', '/test/file/name.yaml.bak')

    # error handling
    mock_move.side_effect = file_util.Error('test error')
    with self.assert_raises_with_validation(files.Error):
      files.Remove('/test/file/name.yaml', backup=True)

  def test_yaml_reader(self):
    temp_file = self.create_tempfile(
        file_path='baz.txt', content='- item4\n- item5\n- item6').full_path
    result = files._YamlReader(temp_file)
    self.assertEqual(result[1], 'item5')


if __name__ == '__main__':
  absltest.main()
