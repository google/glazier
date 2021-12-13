# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Tests for glazier.lib.actions.googet."""

from unittest import mock

from absl.testing import absltest
from glazier.lib.actions import googet


class GooGetTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def setUp(self, bi):
    super(GooGetTest, self).setUp()

    self.pkg = 'test_package_v1'
    self.def_retries = 5
    self.retries = 2
    self.def_sleep = 30
    self.sleep = 1
    self.path = r'C:\ProgramData\GooGet\googet.exe'
    self.flags = ['http://example.com/team-unstable, '
                  'http://example.co.uk/secure-unstable, '
                  'https://example.jp/unstable/ -reinstall whatever']
    self.args = [self.pkg, self.flags, self.path, self.retries, self.sleep]
    self.bi = bi

  @mock.patch.object(googet.googet, 'GooGetInstall', autospec=True)
  def testInstall(self, install):
    install = install.return_value.LaunchGooGet

    # All args
    gi = googet.GooGetInstall([self.args], self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, flags=self.flags, path=self.path,
                               retries=self.retries, sleep=self.sleep,
                               build_info=self.bi)

    # All args multi
    gi = googet.GooGetInstall([self.args, self.args], self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, flags=self.flags, path=self.path,
                               retries=self.retries, sleep=self.sleep,
                               build_info=self.bi)

    # No flags
    self.args = [[self.pkg, None, self.path]]
    gi = googet.GooGetInstall(self.args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, path=self.path, flags=None,
                               retries=self.def_retries, sleep=self.def_sleep,
                               build_info=self.bi)

    # No path
    self.args = [[self.pkg, self.flags]]
    gi = googet.GooGetInstall(self.args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, flags=self.flags, path=None,
                               retries=self.def_retries, sleep=self.def_sleep,
                               build_info=self.bi)

    # Just package
    self.args = [[self.pkg]]
    gi = googet.GooGetInstall(self.args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, path=None, flags=None,
                               retries=self.def_retries, sleep=self.def_sleep,
                               build_info=self.bi)

    # Just package multi
    self.args = [[self.pkg], [self.pkg]]
    gi = googet.GooGetInstall(self.args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, path=None, flags=None,
                               retries=self.def_retries, sleep=self.def_sleep,
                               build_info=self.bi)

    # Package custom retry count and sleep interval
    self.args = [[self.pkg, None, None, self.retries, self.sleep]]
    gi = googet.GooGetInstall(self.args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.pkg, path=None, flags=None,
                               retries=self.retries, sleep=self.sleep,
                               build_info=self.bi)

    # GooGetError
    install.side_effect = googet.googet.Error
    self.assertRaises(googet.ActionError, gi.Run)

    # IndexError
    gi = googet.GooGetInstall([[]], self.bi)
    install.side_effect = googet.googet.Error
    self.assertRaises(googet.ActionError, gi.Run)

  def testValidation(self):
    # Valid calls
    g = googet.GooGetInstall([self.args], self.bi)
    g.Validate()

    # Valid calls multi
    g = googet.GooGetInstall([self.args, self.args], self.bi)
    g.Validate()

    # List not passed
    g = googet.GooGetInstall(['String'], self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Too few args
    g = googet.GooGetInstall([[]], self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Too many args
    g = googet.GooGetInstall([
        [self.pkg, self.flags, self.path, 'abc']], self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Type error
    g = googet.GooGetInstall(self.args.append(1), self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)


if __name__ == '__main__':
  absltest.main()
