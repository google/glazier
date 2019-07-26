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


from absl.testing import absltest
from pyfakefs import fake_filesystem

from glazier.lib import buildinfo
from glazier.lib import googet

import mock


class GoogetTest(absltest.TestCase):

  def setUp(self):
    super(GoogetTest, self).setUp()
    self.install = googet.GoogetInstall()
    self.buildinfo = buildinfo.BuildInfo()
    self.flags = ['whatever', '-reinstall', 'http://example.com/team-%',
                  r'http://example.co.uk/secure-%\%', r'http://%.jp/%\%']

  @mock.patch.object(googet.subprocess, 'call', autospec=True)
  @mock.patch.object(buildinfo.BuildInfo, 'Branch', autospec=True)
  def testLaunchGooget(self, branch, call):
    path = r'C:\ProgramData\Googet\Googet.exe'
    pkg = 'test_package_v1'
    branch.return_value = 'example'

    # Filesystem
    self.filesystem = fake_filesystem.FakeFilesystem()
    googet.os = fake_filesystem.FakeOsModule(self.filesystem)
    self.filesystem.CreateFile(path)

    call.return_value = 0

    # Command called successfully
    self.install.LaunchGooget(pkg, self.buildinfo, path=path, flags=
                              ['http://example.com/team-unstable, '
                               'http://example.co.uk/secure-unstable, '
                               'https://example.jp/unstable/',
                               '-reinstall', 'whatever'])
    cmd_string = (' -noconfirm --root=C:\\ProgramData\\Googet install -sources '
                  'http://example.com/team-unstable, '
                  'http://example.co.uk/secure-unstable, '
                  'https://example.jp/unstable/ -reinstall whatever ')
    cmd = path + cmd_string + pkg
    call.assert_called_with(cmd)

    # String replacement of sources flag was successful
    self.install.LaunchGooget(pkg, self.buildinfo, path=path, flags=self.flags)
    cmd_string = (' -noconfirm --root=C:\\ProgramData\\Googet install -sources '
                  'http://example.com/team-example, '
                  'http://example.co.uk/secure-example%, '
                  'http://example.jp/example% whatever -reinstall ')
    cmd = path + cmd_string + pkg
    call.assert_called_with(cmd)

    # Only pkg
    self.install.LaunchGooget(pkg, self.buildinfo, path=None, flags=None)
    cmd_string = ' -noconfirm --root=C:\\ProgramData\\Googet install '
    cmd = path + cmd_string + pkg
    call.assert_called_with(cmd)

    # No Path
    self.install.LaunchGooget(pkg, self.buildinfo, path=None, flags=self.flags)
    cmd_string = (' -noconfirm --root=C:\\ProgramData\\Googet install -sources '
                  'http://example.com/team-example, '
                  'http://example.co.uk/secure-example%, '
                  'http://example.jp/example% whatever -reinstall ')
    cmd = path + cmd_string + pkg
    call.assert_called_with(cmd)

    # No flags
    self.install.LaunchGooget(pkg, self.buildinfo, path=path, flags=None)
    cmd = path + ' -noconfirm --root=C:\\ProgramData\\Googet install ' + pkg
    call.assert_called_with(cmd)

    # Path does not exist
    with self.assertRaisesRegex(googet.Error,
                                'Cannot find path of Googet binary*'):
      self.install.LaunchGooget(pkg, self.buildinfo, path='C:\\abc\\def\\ghi',
                                flags=self.flags)

    # Empty Package Name
    with self.assertRaisesRegex(googet.Error,
                                'Missing package name for Googet install.'):
      self.install.LaunchGooget('', self.buildinfo, path=path, flags=self.flags)

    # Non zero return value
    call.return_value = 2
    with self.assertRaisesRegex(googet.Error,
                                'Googet command failed with error*'):
      self.install.LaunchGooget(pkg, self.buildinfo, path=path,
                                flags=self.flags)

  def testAddFlags(self):
    branch = 'example'

    # Character replacement
    result = self.install._AddFlags(self.flags, branch)
    self.assertEqual(result, ['-sources http://example.com/team-example, '
                              r'http://example.co.uk/secure-example%, '
                              r'http://example.jp/example%', 'whatever',
                              '-reinstall'], branch)

    # Sources were passed as a string
    with self.assertRaisesRegex(googet.Error,
                                'Googet flags were not passed as a list'):
      self.install._AddFlags('', branch)

    # Root flag passed
    with self.assertRaisesRegex(googet.Error,
                                'Root flag detected, remove flag to continue.'):
      self.install._AddFlags(self.flags + ['--root'], branch)

    # Sources keyword detected
    with self.assertRaisesRegex(googet.Error,
                                'Sources keyword detected*'):
      self.install._AddFlags(self.flags + ['-sources'], branch)

if __name__ == '__main__':
  absltest.main()
