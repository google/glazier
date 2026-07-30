# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copty of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import time
from unittest import mock

from absl.testing import absltest

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import googet
from glazier.lib import test_utils

_REAL_EXISTS = os.path.exists


class GooGetTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(GooGetTest, self).setUp()
    self.install = googet.GooGetInstall()
    self.buildinfo = buildinfo.BuildInfo()
    self.flags = ['whatever', '-reinstall', 'http://example.com/team-%',
                  r'http://example.co.uk/secure-%\%', r'http://%.jp/%\%']

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(googet.execute, 'execute_binary', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get(
      self, unused_sleep, mock_branch, mock_execute_binary, mock_check_winpe):

    path = self.create_tempfile(file_path='googet.exe').full_path

    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    pkg = 'test_package_v1'
    retries = 5
    sleep_dur = 30
    remove = True
    mock_branch.return_value = 'example'

    # Use hosts paths
    mock_check_winpe.return_value = False

    mock_execute_binary.return_value = 0

    # Uninstall Command called successfully
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove,
        path=path,
        flags=[
            (
                'http://example.com/team-unstable, '
                'http://example.co.uk/secure-unstable, '
                'https://example.jp/unstable/'
            ),
            'whatever',
        ],
    )
    cmd = [
        '-noconfirm',
        f'-root={os.path.dirname(path)}',
        'remove',
        '-sources',
        (
            'http://example.com/team-unstable, '
            'http://example.co.uk/secure-unstable, '
            'https://example.jp/unstable/'
        ),
        'whatever',
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    remove = False
    # Install Command called successfully
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove,
        path=path,
        flags=[
            (
                'http://example.com/team-unstable, '
                'http://example.co.uk/secure-unstable, '
                'https://example.jp/unstable/'
            ),
            '-reinstall',
            'whatever',
        ],
    )
    cmd = [
        '-noconfirm',
        f'-root={os.path.dirname(path)}',
        'install',
        '-sources',
        (
            'http://example.com/team-unstable, '
            'http://example.co.uk/secure-unstable, '
            'https://example.jp/unstable/'
        ),
        '-reinstall',
        'whatever',
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # String replacement of sources flag was successful
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove,
        path=path,
        flags=self.flags,
    )
    cmd = [
        '-noconfirm',
        f'-root={os.path.dirname(path)}',
        'install',
        '-sources',
        ('http://example.com/team-example, '
         'http://example.co.uk/secure-example%, '
         'http://example.jp/example%'),
        'whatever',
        '-reinstall',
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # Only pkg
    self.install.LaunchGooGet(
        pkg, retries, sleep_dur, self.buildinfo, remove, path=None, flags=None
    )
    cmd = ['-noconfirm', f'-root={constants.SYS_GOOGETROOT}', 'install']
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # No Path
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove,
        path=None,
        flags=self.flags,
    )
    cmd = [
        '-noconfirm', f'-root={constants.SYS_GOOGETROOT}', 'install',
        '-sources',
        ('http://example.com/team-example, '
         'http://example.co.uk/secure-example%, '
         'http://example.jp/example%'), 'whatever', '-reinstall'
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # No flags
    self.install.LaunchGooGet(
        pkg, retries, sleep_dur, self.buildinfo, remove, path=path, flags=None
    )
    cmd = ['-noconfirm', f'-root={constants.SYS_GOOGETROOT}', 'install']
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # Path does not exist
    with self.assertRaisesRegex(
        googet.Error, 'Cannot find path of GooGet binary*'):
      self.install.LaunchGooGet(
          pkg,
          retries,
          sleep_dur,
          self.buildinfo,
          remove,
          path='C:\\abc\\def\\ghi',
          flags=self.flags,
      )

    # Empty Package Name
    with self.assertRaisesRegex(
        googet.Error, 'Missing package name for GooGet install.'):
      self.install.LaunchGooGet(
          '',
          retries,
          sleep_dur,
          self.buildinfo,
          remove,
          path=path,
          flags=self.flags,
      )

    # Non zero return value
    mock_execute_binary.side_effect = googet.execute.ExecError('some_command')
    with self.assertRaisesRegex(
        googet.Error,
        'GooGet command failed after ' + str(retries) + ' attempts'):
      self.install.LaunchGooGet(
          pkg,
          retries,
          sleep_dur,
          self.buildinfo,
          remove,
          path=path,
          flags=self.flags,
      )

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True, spec_set=True)
  @mock.patch.object(
      googet.execute, 'execute_binary', autospec=True, spec_set=True
  )
  @mock.patch.object(googet.os.path, 'exists', autospec=True, spec_set=True)
  @mock.patch.object(
      buildinfo.BuildInfo, 'Branch', autospec=True, spec_set=True
  )
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get_local_success(
      self,
      unused_sleep,
      mock_branch,
      mock_exists,
      mock_execute_binary,
      mock_check_winpe,
  ):
    pkg = 'test_package_v1'
    local_dir = r'X:\Program Files\Glazier\resources'
    local_path = os.path.normpath(os.path.join(local_dir, f'{pkg}.goo'))

    def exists_side_effect(path_param):
      norm_param = os.path.normpath(str(path_param)).replace('\\', '/')
      norm_local = os.path.normpath(local_path).replace('\\', '/')
      if norm_param == norm_local:
        return True
      return _REAL_EXISTS(path_param)

    mock_exists.side_effect = exists_side_effect

    path = self.create_tempfile(file_path='googet.exe').full_path
    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    retries = 5
    sleep_dur = 30
    mock_branch.return_value = 'example'
    mock_check_winpe.return_value = False
    mock_execute_binary.return_value = 0

    # Local Install (local file exists)
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=False,
        path=path,
        flags=[
            local_dir,
            'https://googet.example.com/repos/example-%',
            '-reinstall',
            'whatever',
        ],
    )
    cmd = [
        '-noconfirm',
        f'-root={temp_dir}',
        'install',
        '-reinstall',
        'whatever',
    ]
    cmd.extend([local_path])
    mock_execute_binary.assert_called_with(path, cmd)

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True, spec_set=True)
  @mock.patch.object(
      googet.execute, 'execute_binary', autospec=True, spec_set=True
  )
  @mock.patch.object(googet.os.path, 'exists', autospec=True, spec_set=True)
  @mock.patch.object(
      buildinfo.BuildInfo, 'Branch', autospec=True, spec_set=True
  )
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get_local_fallback(
      self,
      unused_sleep,
      mock_branch,
      mock_exists,
      mock_execute_binary,
      mock_check_winpe,
  ):
    pkg = 'test_package_v1'
    local_dir = r'X:\Program Files\Glazier\resources'
    local_path = os.path.normpath(os.path.join(local_dir, f'{pkg}.goo'))

    def exists_side_effect(path_param):
      norm_param = os.path.normpath(str(path_param)).replace('\\', '/')
      norm_local = os.path.normpath(local_path).replace('\\', '/')
      if norm_param == norm_local:
        return False
      return _REAL_EXISTS(path_param)

    mock_exists.side_effect = exists_side_effect

    path = self.create_tempfile(file_path='googet.exe').full_path
    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    retries = 5
    sleep_dur = 30
    mock_branch.return_value = 'example'
    mock_check_winpe.return_value = False
    mock_execute_binary.return_value = 0

    # Local Install fails fallback to remote (FileNotFound)
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=False,
        path=path,
        flags=[
            local_dir,
            'https://googet.example.com/repos/example',
            '-reinstall',
            'whatever',
        ],
    )
    cmd = [
        '-noconfirm',
        f'-root={temp_dir}',
        'install',
        '-sources',
        (
            r'X:\Program'
            r' Files\Glazier\resources,'
            r' https://googet.example.com/repos/example'
        ),
        '-reinstall',
        'whatever',
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True, spec_set=True)
  @mock.patch.object(
      googet.execute, 'execute_binary', autospec=True, spec_set=True
  )
  @mock.patch.object(googet.os.path, 'exists', autospec=True, spec_set=True)
  @mock.patch.object(
      buildinfo.BuildInfo, 'Branch', autospec=True, spec_set=True
  )
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get_local_uninstall(
      self,
      unused_sleep,
      mock_branch,
      mock_exists,
      mock_execute_binary,
      mock_check_winpe,
  ):
    mock_exists.side_effect = _REAL_EXISTS

    path = self.create_tempfile(file_path='googet.exe').full_path
    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    pkg = 'test_package_v1'
    retries = 5
    sleep_dur = 30
    mock_branch.return_value = 'example'
    mock_check_winpe.return_value = False
    mock_execute_binary.return_value = 0

    # Uninstall ignores local files (even if GetResourceFileName would succeed)
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=True,
        path=path,
        flags=[
            'https://googet.example.com/repos/example',
            'whatever',
        ],
    )
    cmd = [
        '-noconfirm',
        f'-root={temp_dir}',
        'remove',
        '-sources',
        'https://googet.example.com/repos/example',
        'whatever',
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True, spec_set=True)
  @mock.patch.object(
      googet.execute, 'execute_binary', autospec=True, spec_set=True
  )
  @mock.patch.object(googet.os.path, 'exists', autospec=True, spec_set=True)
  @mock.patch.object(
      buildinfo.BuildInfo, 'Branch', autospec=True, spec_set=True
  )
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get_local_invalid_flags(
      self,
      unused_sleep,
      mock_branch,
      mock_exists,
      mock_execute_binary,
      mock_check_winpe,
  ):
    mock_exists.side_effect = _REAL_EXISTS

    path = self.create_tempfile(file_path='googet.exe').full_path
    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    pkg = 'test_package_v1'
    retries = 5
    sleep_dur = 30
    mock_branch.return_value = 'example'
    mock_check_winpe.return_value = False
    mock_execute_binary.return_value = 0

    # Flags is not a list (string)
    self.assertRaises(
        googet.GooGetFlagError,
        self.install.LaunchGooGet,
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=False,
        path=path,
        flags='not-a-list',
    )

    # Flags is not a list (integer)
    self.assertRaises(
        googet.GooGetFlagError,
        self.install.LaunchGooGet,
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=False,
        path=path,
        flags=123,
    )

  @mock.patch.object(googet.winpe, 'check_winpe', autospec=True, spec_set=True)
  @mock.patch.object(
      googet.execute, 'execute_binary', autospec=True, spec_set=True
  )
  @mock.patch.object(
      googet.GooGetInstall, '_FindLocalPackage', autospec=True, spec_set=True
  )
  @mock.patch.object(
      buildinfo.BuildInfo, 'Branch', autospec=True, spec_set=True
  )
  @mock.patch.object(time, 'sleep', return_value=None)
  def test_launch_goo_get_local_no_flags_mock_path(
      self,
      unused_sleep,
      mock_branch,
      mock_find_local,
      mock_execute_binary,
      mock_check_winpe,
  ):
    pkg = 'test_package_v1'
    local_path = r'C:\mock_local_path\test_package_v1.goo'
    mock_find_local.return_value = local_path

    path = self.create_tempfile(file_path='googet.exe').full_path
    temp_dir = os.path.dirname(path)
    self.patch_constant(constants, 'SYS_GOOGETROOT', temp_dir)

    retries = 5
    sleep_dur = 30
    mock_branch.return_value = 'example'
    mock_check_winpe.return_value = False
    mock_execute_binary.return_value = 0

    # Local Install succeeds even if flags is None (not passed in kwargs)
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        remove=False,
        path=path,
    )
    cmd = [
        '-noconfirm',
        f'-root={temp_dir}',
        'install',
    ]
    cmd.extend([local_path])
    mock_execute_binary.assert_called_with(path, cmd)

  def test_add_flags(self):
    branch = 'example'

    # Character replacement
    result = self.install._AddFlags(self.flags, branch)
    self.assertEqual(result, [
        '-sources',
        (
            'http://example.com/team-example, '
            'http://example.co.uk/secure-example%, '
            'http://example.jp/example%'
        ),
        'whatever', '-reinstall'
    ])

    # Sources were passed as a string
    with self.assertRaisesRegex(
        googet.Error, 'GooGet flags were not passed as a list'):
      self.install._AddFlags('', branch)

    # Root flag passed
    with self.assertRaisesRegex(
        googet.Error, 'Root flag detected, remove flag to continue.'):
      self.install._AddFlags(self.flags + ['-root'], branch)

    # Sources keyword detected
    with self.assertRaisesRegex(
        googet.Error, 'Sources keyword detected*'):
      self.install._AddFlags(self.flags + ['-sources'], branch)

if __name__ == '__main__':
  absltest.main()
