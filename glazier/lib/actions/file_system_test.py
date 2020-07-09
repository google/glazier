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
from pyfakefs import fake_filesystem
from pyfakefs import fake_filesystem_shutil
from glazier.lib.actions import file_system
import mock


class FileSystemTest(absltest.TestCase):

  def setUp(self):
    super(FileSystemTest, self).setUp()
    # fake filesystem
    fs = fake_filesystem.FakeFilesystem()
    fs.CreateDirectory(r'/stage')
    fs.CreateFile(r'/stage/file1.txt', contents='file1')
    fs.CreateFile(r'/stage/file2.txt', contents='file2')
    self.fake_open = fake_filesystem.FakeFileOpen(fs)
    file_system.os = fake_filesystem.FakeOsModule(fs)
    file_system.shutil = fake_filesystem_shutil.FakeShutilModule(fs)
    file_system.open = self.fake_open
    self.fs = fs

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDirException(self, build_info):
    cd = file_system.CopyDir([r'/stage', r'/stage'], build_info)
    self.assertRaises(file_system.ActionError, cd.Run)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyDirMissingArgs(self, build_info):
    cd = file_system.CopyDir([r'/stage'], build_info)
    self.assertRaises(file_system.ValidationError, cd.Validate)
    self.assertRaises(file_system.ActionError, cd.Run)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileBadPath(self, build_info):
    src1 = r'/missing.txt'
    dst1 = r'/windows/glazier/glazier.log'
    cf = file_system.CopyFile([src1, dst1], build_info)
    self.assertRaises(file_system.ActionError, cf.Run)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileInvalidArgs(self, build_info):
    cf = file_system.CopyFile([r'/file1.txt'], build_info)
    self.assertRaises(file_system.ActionError, cf.Run)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testCopyFileInvalidMultiArgs(self, build_info):
    cf = file_system.MultiCopyFile([r'/file1.txt'], build_info)
    self.assertRaises(file_system.ActionError, cf.Run)

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
    md = file_system.MkDir(['/stage/subdir1/subdir2'], build_info)
    md.Run()
    self.assertTrue(file_system.os.path.exists('/stage/subdir1/subdir2'))
    # bad path
    md = file_system.MkDir([r'/stage/file1.txt'], build_info)
    self.assertRaises(file_system.ActionError, md.Run)
    # bad args
    md = file_system.MkDir([], build_info)
    self.assertRaises(file_system.ActionError, md.Run)

  def testMkdirValidate(self):
    md = file_system.MkDir('String', None)
    self.assertRaises(file_system.ValidationError, md.Validate)
    md = file_system.MkDir(['/tmp/some/dir', '/tmp/some/other/dir'], None)
    self.assertRaises(file_system.ValidationError, md.Validate)
    md = file_system.MkDir([1], None)
    self.assertRaises(file_system.ValidationError, md.Validate)
    md = file_system.MkDir(['/tmp/some/dir'], None)
    md.Validate()

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
    build_info.CachePath.return_value = '/test/cache/path'
    sc = file_system.SetupCache([], build_info)
    sc.Run()
    self.assertTrue(file_system.os.path.exists('/test/cache/path'))

  def testSetupCacheValidate(self):
    sc = file_system.SetupCache('String', None)
    self.assertRaises(file_system.ValidationError, sc.Validate)
    sc = file_system.SetupCache([], None)
    sc.Validate()


if __name__ == '__main__':
  absltest.main()
