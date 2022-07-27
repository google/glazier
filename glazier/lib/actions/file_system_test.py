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

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import file_util
from glazier.lib.actions import file_system

from pyfakefs.fake_filesystem_unittest import Patcher


class CopyDirTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(self, mock_buildinfo):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      cd = file_system.CopyDir([r'/stage', r'/root/copied'], mock_buildinfo)
      cd.Validate()
      cd.Run()
      self.assertTrue(patcher.fs.exists(r'/root/copied/file1.txt'))
      self.assertTrue(patcher.fs.exists(r'/root/copied/file2.txt'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_copy_with_remove(self, mock_buildinfo):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      patcher.fs.create_file(r'/stage/file1.txt', contents='file1')
      patcher.fs.create_file(r'/stage/file2.txt', contents='file2')
      cd = file_system.CopyDir(
          [r'/stage', r'/root/copied', True], mock_buildinfo)
      cd.Validate()
      cd.Run()
      self.assertTrue(patcher.fs.exists(r'/root/copied/file1.txt'))
      self.assertTrue(patcher.fs.exists(r'/root/copied/file2.txt'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_exception(self, mock_buildinfo):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/stage')
      with self.assertRaises(file_system.ActionError):
        file_system.CopyDir([r'/stage', r'/stage'], mock_buildinfo).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_missing_args(self, mock_buildinfo):
    cd = file_system.CopyDir([r'/stage'], mock_buildinfo)
    with self.assertRaises(file_system.ValidationError):
      cd.Validate()
    with self.assertRaises(file_system.ActionError):
      cd.Run()


class MultiCopyDirTest(parameterized.TestCase):

  @mock.patch.object(file_system.shutil, 'copytree', autospec=True)
  @mock.patch.object(file_system.shutil, 'rmtree', autospec=True)
  @mock.patch.object(file_system.os.path, 'exists', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(
      self, mock_build_info, mock_exists, mock_rmtree, mock_copytree):

    # exists=True, remove_existing=True
    copydir_args1 = [r'/src/dir/one/', r'/dst/dir/one/', True]
    # exists=True, remove_existing=False
    copydir_args2 = [r'/src/dir/two/', r'/dst/dir/two/', False]
    # exists=True, remove_existing=None
    copydir_args3 = [r'/src/dir/three/', r'/dst/dir/three/']
    # exists=False, remove_existing=True
    copydir_args4 = [r'/src/dir/four/', r'/dst/dir/four/', True]
    # exists=False, remove_existing=False
    copydir_args5 = [r'/src/dir/five/', r'/dst/dir/five/', False]
    # exists=False, remove_existing=None
    copydir_args6 = [r'/src/dir/six/', r'/dst/dir/six/']

    mock_exists.side_effect = [True] * 3 + [False] * 3

    multicopydir_args = [
        copydir_args1, copydir_args2, copydir_args3, copydir_args4,
        copydir_args5, copydir_args6]
    file_system.MultiCopyDir(
        multicopydir_args, mock_build_info).Run()

    self.assertEqual(mock_exists.call_count, 6)
    mock_rmtree.assert_called_once_with(r'/dst/dir/one/')
    mock_copytree.assert_has_calls([
        mock.call(r'/src/dir/one/', r'/dst/dir/one/'),
        mock.call(r'/src/dir/two/', r'/dst/dir/two/'),
        mock.call(r'/src/dir/three/', r'/dst/dir/three/'),
        mock.call(r'/src/dir/four/', r'/dst/dir/four/'),
        mock.call(r'/src/dir/five/', r'/dst/dir/five/'),
        mock.call(r'/src/dir/six/', r'/dst/dir/six/'),
    ])

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_invalid_multi_args(self, mock_build_info):
    with self.assertRaises(file_system.ActionError):
      copydir_args = [r'/src/dir/one/']
      file_system.MultiCopyDir([copydir_args], mock_build_info).Run()

  # NOTE: Reverse decoration is intentional, due to @parameterized and @mock.
  @parameterized.parameters(
      ([r'/src/dir/one/', r'/dst/dir/one/', True],),
      ([r'/src/dir/two/', r'/dst/dir/two/', False],),
      ([r'/src/dir/three/', r'/dst/dir/three/'],),
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_validate_valid_args(self, copydir_args, mock_build_info):
    multicopydir_args = [copydir_args]
    file_system.MultiCopyDir(multicopydir_args, mock_build_info).Validate()

  # NOTE: Reverse decoration is intentional, due to @parameterized and @mock.
  @parameterized.parameters(
      ('String',),  # wrong overall type
      (['/src/dir/one/'],),  # too short
      (['a', 'b', 'c', 'd'],),  # too long
      ([2, '/dst/dir/two/', True],),  # wrong type [0]
      (['/src/dir/three/', 3, True],),  # wrong type [1]
      (['/src/dir/four/', '/dst/dir/four/', 4],),  # wrong type [2]
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_validate_invalid_args(self, copydir_args, mock_build_info):
    with self.assertRaises(file_system.ValidationError):
      multicopydir_args = [copydir_args]
      file_system.MultiCopyDir(multicopydir_args, mock_build_info).Validate()


class MultiCopyFileTest(parameterized.TestCase):

  @mock.patch.object(file_util, 'Copy', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(self, mock_buildinfo, mock_copy):
    src1 = r'/stage/file1.txt'
    dst1 = r'/windows/glazier/glazier.log'
    src2 = r'/stage/file2.txt'
    dst2 = r'/windows/glazier/other.log'
    file_system.MultiCopyFile(
        [[src1, dst1], [src2, dst2]], mock_buildinfo).Run()
    mock_copy.assert_has_calls([mock.call(src1, dst1), mock.call(src2, dst2)])

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_invalid_multi_args(self, mock_buildinfo):
    with self.assertRaises(file_system.ActionError):
      file_system.MultiCopyFile([r'/file1.txt'], mock_buildinfo).Run()

  @parameterized.named_parameters(
      ('_invalid_type_1', 'String', None),
      ('_invalid_type_2', ['String'], None),
      ('_invalid_args_length', [[1, 2, 3]], None),
      ('_invalid_type_3', [[1, '/tmp/dest.txt']], None),
      ('_invalid_type_4', [['/tmp/src.txt', 2]], None),
  )
  def test_validation_error(self, action_args, build_info):
    cf = file_system.MultiCopyFile(action_args, build_info)
    with self.assertRaises(file_system.ValidationError):
      cf.Validate()

  def test_validation_success(self):
    cf = file_system.MultiCopyFile([['/tmp/src1.txt', '/tmp/dest1.txt'],
                                    ['/tmp/src2.txt', '/tmp/dest2.txt']], None)
    cf.Validate()


class CopyFileTest(absltest.TestCase):

  @mock.patch.object(file_util, 'Copy', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_error(self, mock_buildinfo, mock_copy):
    src1 = r'/missing.txt'
    dst1 = r'/windows/glazier/glazier.log'
    mock_copy.side_effect = file_util.Error('error')
    with self.assertRaises(file_system.ActionError):
      file_system.CopyFile([src1, dst1], mock_buildinfo).Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_invalid_args(self, mock_buildinfo):
    with self.assertRaises(file_system.ActionError):
      file_system.CopyFile([r'/file1.txt'], mock_buildinfo).Run()


class MkDirTest(parameterized.TestCase):

  @mock.patch.object(file_util, 'CreateDirectories', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(self, mock_buildinfo, mock_createdirectories):
    file_system.MkDir(['/stage/subdir1/subdir2'], mock_buildinfo).Run()
    mock_createdirectories.assert_called_with('/stage/subdir1/subdir2')
    # bad path
    mock_createdirectories.side_effect = file_util.Error('error')
    with self.assertRaises(file_system.ActionError):
      file_system.MkDir([r'/stage/file1.txt'], mock_buildinfo).Run()
    # bad args
    with self.assertRaises(file_system.ActionError):
      file_system.MkDir([], mock_buildinfo).Run()

  @parameterized.named_parameters(
      ('_invalid_type_1', 'String', None),
      ('_invalid_args_length', ['/tmp/some/dir', '/tmp/some/other/dir'], None),
      ('_invalid_type_2', [1], None),
  )
  def test_validation_error(self, action_args, build_info):
    with self.assertRaises(file_system.ValidationError):
      file_system.MkDir(action_args, build_info).Validate()

  def test_validation_success(self):
    file_system.MkDir(['/tmp/some/dir'], None).Validate()


class RmDirTest(parameterized.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(self, mock_buildinfo):
    with Patcher() as patcher:
      patcher.fs.create_dir(r'/test1')
      patcher.fs.create_dir(r'/test2')
      self.assertTrue(patcher.fs.exists('/test2'))
      file_system.RmDir(['/test1', '/test2'], mock_buildinfo).Run()
      self.assertFalse(patcher.fs.exists('/test2'))

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_exception(self, mock_buildinfo):
    with self.assertRaises(file_system.ActionError):
      file_system.RmDir(['/missing'], mock_buildinfo).Run()

  @parameterized.named_parameters(
      ('_invalid_args_length', [], None),
      ('_invalid_arg_type', [12345], None),
  )
  def test_validation_error(self, action_args, build_info):
    with self.assertRaises(file_system.ValidationError):
      file_system.RmDir(action_args, build_info).Validate()

  @parameterized.named_parameters(
      ('_single', [r'D:\Glazier'], None),
      ('_multiple', [r'C:\Glazier', r'D:\Glazier'], None),
  )
  def test_validation_success(self, action_args, build_info):
    file_system.RmDir(action_args, build_info).Validate()


class SetupCacheTest(absltest.TestCase):

  @mock.patch.object(file_util, 'CreateDirectories', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_success(self, mock_buildinfo, create):
    mock_buildinfo.CachePath.return_value = '/test/cache/path'
    file_system.SetupCache([], mock_buildinfo).Run()
    create.assert_called_with('/test/cache/path')

  def test_validate(self):
    sc = file_system.SetupCache('String', None)
    with self.assertRaises(file_system.ValidationError):
      sc.Validate()
    sc = file_system.SetupCache([], None)
    sc.Validate()


if __name__ == '__main__':
  absltest.main()
