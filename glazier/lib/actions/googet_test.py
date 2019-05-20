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
from absl.testing import absltest
from glazier.lib.actions import googet
import mock


class GoogetTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def setUp(self, bi):
    super(GoogetTest, self).setUp()

    # Mock values
    self.mock_pkg = 'test_package_v1'
    self.mock_path = r'C:\ProgramData\Googet\Googet.exe'
    self.mock_flags = ('http://example.com/team-unstable, '
                       'http://example.co.uk/secure-unstable, '
                       'https://example.jp/unstable/ -reinstall whatever')
    self.mock_args = [self.mock_pkg, self.mock_flags, self.mock_path]
    self.bi = bi

  @mock.patch.object(googet.googet, 'GoogetInstall', autospec=True)
  def testInstall(self, mock_install):

    # All args
    install = mock_install.return_value.LaunchGooget
    gi = googet.GoogetInstall(self.mock_args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.mock_pkg, build_info=self.bi,
                               path=self.mock_path, flags=self.mock_flags)

    # No flags
    self.mock_args = [self.mock_pkg, None, self.mock_path]
    gi = googet.GoogetInstall(self.mock_args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.mock_pkg, build_info=self.bi,
                               path=self.mock_path, flags=None)

    # No path
    self.mock_args = [self.mock_pkg, self.mock_flags]
    gi = googet.GoogetInstall(self.mock_args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.mock_pkg, build_info=self.bi,
                               path=None, flags=self.mock_flags)

    # Just package
    self.mock_args = [self.mock_pkg]
    gi = googet.GoogetInstall(self.mock_args, self.bi)
    gi.Run()
    install.assert_called_with(pkg=self.mock_pkg, build_info=self.bi,
                               path=None, flags=None)

    # GoogetError
    install.side_effect = googet.googet.Error
    self.assertRaises(googet.ActionError, gi.Run)

    # IndexError
    gi = googet.GoogetInstall([], self.bi)
    install.side_effect = googet.googet.Error
    self.assertRaises(googet.ActionError, gi.Run)

  def testAddValidation(self):
    # Valid calls
    g = googet.GoogetInstall(self.mock_args, self.bi)
    g.Validate()

    # List not passed
    g = googet.GoogetInstall('String', self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Too few args
    g = googet.GoogetInstall([], self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Too many args
    g = googet.GoogetInstall(self.mock_args + ['abc'], self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)

    # Type error
    g = googet.GoogetInstall(self.mock_args.append(1), self.bi)
    self.assertRaises(googet.ValidationError, g.Validate)


if __name__ == '__main__':
  absltest.main()
