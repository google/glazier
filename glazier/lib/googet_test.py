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

"""Tests for glazier.lib.googet."""

import os
import time
from unittest import mock

from absl.testing import absltest

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import googet
from glazier.lib import test_utils


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
    mock_branch.return_value = 'example'

    # Use hosts paths
    mock_check_winpe.return_value = False

    mock_execute_binary.return_value = 0

    # Command called successfully
    self.install.LaunchGooGet(
        pkg,
        retries,
        sleep_dur,
        self.buildinfo,
        path=path,
        flags=[('http://example.com/team-unstable, '
                'http://example.co.uk/secure-unstable, '
                'https://example.jp/unstable/'), '-reinstall', 'whatever'])
    cmd = [
        '-noconfirm', f'-root={os.path.dirname(path)}', 'install', '-sources',
        ('http://example.com/team-unstable, '
         'http://example.co.uk/secure-unstable, '
         'https://example.jp/unstable/'), '-reinstall', 'whatever'
    ]
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # String replacement of sources flag was successful
    self.install.LaunchGooGet(
        pkg, retries, sleep_dur, self.buildinfo, path=path, flags=self.flags)
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
        pkg, retries, sleep_dur, self.buildinfo, path=None, flags=None)
    cmd = ['-noconfirm', f'-root={constants.SYS_GOOGETROOT}', 'install']
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # No Path
    self.install.LaunchGooGet(
        pkg, retries, sleep_dur, self.buildinfo, path=None, flags=self.flags)
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
        pkg, retries, sleep_dur, self.buildinfo, path=path, flags=None)
    cmd = ['-noconfirm', f'-root={constants.SYS_GOOGETROOT}', 'install']
    cmd.extend([pkg])
    mock_execute_binary.assert_called_with(path, cmd)

    # Path does not exist
    with self.assertRaisesRegex(
        googet.Error, 'Cannot find path of GooGet binary*'):
      self.install.LaunchGooGet(
          pkg, retries, sleep_dur, self.buildinfo, path='C:\\abc\\def\\ghi',
          flags=self.flags)

    # Empty Package Name
    with self.assertRaisesRegex(
        googet.Error, 'Missing package name for GooGet install.'):
      self.install.LaunchGooGet(
          '', retries, sleep_dur, self.buildinfo, path=path, flags=self.flags)

    # Non zero return value
    mock_execute_binary.side_effect = googet.execute.ExecError('some_command')
    with self.assertRaisesRegex(
        googet.Error,
        'GooGet command failed after ' + str(retries) + ' attempts'):
      self.install.LaunchGooGet(
          pkg, retries, sleep_dur, self.buildinfo, path=path, flags=self.flags)

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
