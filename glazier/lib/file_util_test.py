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

from absl.testing import absltest

from glazier.lib import file_util

from pyfakefs.fake_filesystem_unittest import Patcher


class FileUtilTest(absltest.TestCase):

  def testCopy(self):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      src1 = r'/stage/file1.txt'
      dst1 = r'/windows/glazier/glazier.log'
      file_util.Copy(src1, dst1)
      self.assertTrue(patcher.fs.exists(r'/windows/glazier/glazier.log'))

  def testCopyBadPath(self):
    with Patcher():
      src1 = r'/missing.txt'
      dst1 = r'/windows/glazier/glazier.log'
      with self.assertRaises(file_util.Error):
        file_util.Copy(src1, dst1)

  def testCreateDirectories(self):
    with Patcher() as patcher:
      patcher.fs.create_file('/test')
      self.assertRaises(file_util.Error, file_util.CreateDirectories,
                        '/test/file.txt')
      file_util.CreateDirectories('/tmp/test/path/file.log')
      self.assertTrue(patcher.fs.exists('/tmp/test/path'))

  def testRemove(self):
    with Patcher() as patcher:
      patcher.fs.create_file('/test/file.txt')
      file_util.Remove('/test/file.txt')
      self.assertFalse(patcher.fs.exists('/test/file.txt'))
      file_util.Remove('/test/file2.txt')  # should succeed silently


if __name__ == '__main__':
  absltest.main()
