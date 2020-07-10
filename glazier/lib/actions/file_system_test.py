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
"""Tests for glazier.lib.actions.file_system."""

from absl.testing import absltest

from glazier.lib.actions import file_system

import mock
from pyfakefs.fake_filesystem_unittest import Patcher


class FileSystemTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDir(self, build_info):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      cd = file_system.CopyDir([r'/stage', r'/root/copied'], build_info)
      cd.Validate()
      cd.Run()
      self.assertTrue(patcher.fs.Exists(r'/root/copied/file1.txt'))
      self.assertTrue(patcher.fs.Exists(r'/root/copied/file2.txt'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDirWithRemove(self, build_info):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      cd = file_system.CopyDir([r'/stage', r'/root/copied', True], build_info)
      cd.Validate()
      cd.Run()
      self.assertTrue(patcher.fs.Exists(r'/root/copied/file1.txt'))
      self.assertTrue(patcher.fs.Exists(r'/root/copied/file2.txt'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDirException(self, build_info):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      with self.assertRaises(file_system.ActionError):
        file_system.CopyDir([r'/stage', r'/stage'], build_info).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDirMissingArgs(self, build_info):
    cd = file_system.CopyDir([r'/stage'], build_info)
    with self.assertRaises(file_system.ValidationError):
      cd.Validate()
    with self.assertRaises(file_system.ActionError):
      cd.Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFile(self, build_info):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      src1 = r'/stage/file1.txt'
      dst1 = r'/windows/glazier/glazier.log'
      src2 = r'/stage/file2.txt'
      dst2 = r'/windows/glazier/other.log'
      file_system.MultiCopyFile([[src1, dst1], [src2, dst2]], build_info).Run()
      self.assertTrue(patcher.fs.Exists(r'/windows/glazier/glazier.log'))
      self.assertTrue(patcher.fs.Exists(r'/windows/glazier/other.log'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileBadPath(self, build_info):
    src1 = r'/missing.txt'
    dst1 = r'/windows/glazier/glazier.log'
    with self.assertRaises(file_system.ActionError):
      file_system.CopyFile([src1, dst1], build_info).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileInvalidArgs(self, build_info):
    with self.assertRaises(file_system.ActionError):
      file_system.CopyFile([r'/file1.txt'], build_info).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileInvalidMultiArgs(self, build_info):
    with self.assertRaises(file_system.ActionError):
      file_system.MultiCopyFile([r'/file1.txt'], build_info).Run()

  def testCopyFileValidate(self):
    cf = file_system.MultiCopyFile('String', None)
    self.assertRaises(file_system.ValidationError, cf.Validate)
    cf = file_system.MultiCopyFile(['String'], None)
    self.assertRaises(file_system.ValidationError, cf.Validate)
    cf = file_system.MultiCopyFile([[1, 2, 3]], None)
    self.assertRaises(file_system.ValidationError, cf.Validate)
    cf = file_system.MultiCopyFile([[1, '/tmp/dest.txt']], None)
    self.assertRaises(file_system.ValidationError, cf.Validate)
    cf = file_system.MultiCopyFile([['/tmp/src.txt', 2]], None)
    self.assertRaises(file_system.ValidationError, cf.Validate)
    cf = file_system.MultiCopyFile([['/tmp/src1.txt', '/tmp/dest1.txt'],
                                    ['/tmp/src2.txt', '/tmp/dest2.txt']], None)
    cf.Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testMkdir(self, build_info):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      file_system.MkDir(['/stage/subdir1/subdir2'], build_info).Run()
      self.assertTrue(file_system.os.path.exists('/stage/subdir1/subdir2'))
      # bad path
      with self.assertRaises(file_system.ActionError):
        file_system.MkDir([r'/stage/file1.txt'], build_info).Run()
      # bad args
      with self.assertRaises(file_system.ActionError):
        file_system.MkDir([], build_info).Run()

  def testMkdirValidate(self):
    with self.assertRaises(file_system.ValidationError):
      file_system.MkDir('String', None).Validate()
    with self.assertRaises(file_system.ValidationError):
      file_system.MkDir(['/tmp/some/dir', '/tmp/some/other/dir'],
                        None).Validate()
    with self.assertRaises(file_system.ValidationError):
      file_system.MkDir([1], None).Validate()
    file_system.MkDir(['/tmp/some/dir'], None).Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRmDir(self, build_info):
    with Patcher() as patcher:
      patcher.fs.CreateDirectory(r'/test1')
      patcher.fs.CreateDirectory(r'/test2')
      self.assertTrue(file_system.os.path.exists('/test2'))
      file_system.RmDir(['/test1', '/test2'], build_info).Run()
      self.assertFalse(file_system.os.path.exists('/test2'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRmDirException(self, build_info):
    with self.assertRaises(file_system.ActionError):
      file_system.RmDir(['/missing'], build_info).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testRmDirValidate(self, build_info):
    with self.assertRaises(file_system.ValidationError):
      file_system.RmDir([], build_info).Validate()
    with self.assertRaises(file_system.ValidationError):
      file_system.RmDir([12345], build_info).Validate()
    file_system.RmDir([r'D:\Glazier'], build_info).Validate()
    file_system.RmDir([r'C:\Glazier', r'D:\Glazier'], build_info).Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testSetupCache(self, build_info):
    with Patcher():
      build_info.CachePath.return_value = '/test/cache/path'
      file_system.SetupCache([], build_info).Run()
      self.assertTrue(file_system.os.path.exists('/test/cache/path'))

  def testSetupCacheValidate(self):
    sc = file_system.SetupCache('String', None)
    self.assertRaises(file_system.ValidationError, sc.Validate)
    sc = file_system.SetupCache([], None)
    sc.Validate()


if __name__ == '__main__':
  absltest.main()
