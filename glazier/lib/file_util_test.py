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

"""Tests for glazier.lib.file_util."""

import os
from unittest import mock
from absl.testing import absltest

from glazier.lib import file_util
from glazier.lib import test_utils


class FileUtilTest(test_utils.GlazierTestCase):

  def test_copy(self):

    src1 = self.create_tempfile(file_path='file1.txt', content='file1')
    self.create_tempfile(file_path='file2.txt', content='file2')
    dst1 = self.create_tempfile(file_path='glazier.log')
    file_util.Copy(src1, dst1)

    self.assertTrue(os.path.exists(dst1))
    with open(dst1) as f:
      self.assertEqual('file1', f.read())

  def test_copy_bad_path(self):
    src1 = r'/missing.txt'
    dst1 = self.create_tempfile(file_path='glazier.log')
    with self.assert_raises_with_validation(file_util.FileCopyError):
      file_util.Copy(src1, dst1)

  @mock.patch.object(os, 'makedirs')
  @mock.patch.object(os.path, 'isdir')
  def test_create_directories_error(self, mock_isdir, mock_makedirs):

    mock_isdir.return_value = False
    mock_makedirs.side_effect = OSError

    with self.assert_raises_with_validation(file_util.DirectoryCreationError):
      file_util.CreateDirectories('/some/path/to/file.txt')

  @mock.patch.object(os, 'makedirs')
  @mock.patch.object(os.path, 'isdir')
  def test_create_directories_success(self, mock_isdir, mock_makedirs):

    mock_isdir.return_value = False
    file_util.CreateDirectories('/some/path/to/file.txt')

    self.assertTrue(mock_makedirs.called)

  def test_remove(self):
    temp_file = self.create_tempfile(file_path='file.txt')
    file_util.Remove(temp_file)
    self.assertFalse(os.path.exists(temp_file))
    file_util.Remove('/test/file2.txt')  # should succeed silently


if __name__ == '__main__':
  absltest.main()
