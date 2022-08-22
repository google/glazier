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
from absl.testing import parameterized
from glazier.lib import test_utils
from glazier.lib.actions import googet

PKG = 'test_package_v1'
FLAGS = [('http://example.com/team-unstable, '
          'http://example.co.uk/secure-unstable, '
          'https://example.jp/unstable/ -reinstall whatever')]
PATH = r'C:\ProgramData\GooGet\googet.exe'
RETRIES = 2
DEFAULT_RETRIES = 5
SLEEP = 1
DEFAULT_SLEEP = 30


class GooGetTest(test_utils.GlazierTestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(googet.googet, 'GooGetInstall', autospec=True)
  def test_install_success(self, mock_install, mock_build_info):

    mock_install = mock_install.return_value.LaunchGooGet

    # All args
    action_args = [[PKG, FLAGS, PATH, RETRIES, SLEEP]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        flags=FLAGS,
        path=PATH,
        retries=RETRIES,
        sleep=SLEEP,
        build_info=mock_build_info)

    # All args multi
    action_args = [[PKG, FLAGS, PATH, RETRIES, SLEEP],
                   [PKG, FLAGS, PATH, RETRIES, SLEEP]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        flags=FLAGS,
        path=PATH,
        retries=RETRIES,
        sleep=SLEEP,
        build_info=mock_build_info)

    # No flags
    action_args = [[PKG, None, PATH]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        path=PATH,
        flags=None,
        retries=DEFAULT_RETRIES,
        sleep=DEFAULT_SLEEP,
        build_info=mock_build_info)

    # No path
    action_args = [[PKG, FLAGS]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        flags=FLAGS,
        path=None,
        retries=DEFAULT_RETRIES,
        sleep=DEFAULT_SLEEP,
        build_info=mock_build_info)

    # Just package
    action_args = [[PKG]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        path=None,
        flags=None,
        retries=DEFAULT_RETRIES,
        sleep=DEFAULT_SLEEP,
        build_info=mock_build_info)

    # Just package multi
    action_args = [[PKG], [PKG]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        path=None,
        flags=None,
        retries=DEFAULT_RETRIES,
        sleep=DEFAULT_SLEEP,
        build_info=mock_build_info)

    # Package custom retry count and sleep interval
    action_args = [[PKG, None, None, RETRIES, SLEEP]]
    gi = googet.GooGetInstall(action_args, mock_build_info)
    gi.Run()
    mock_install.assert_called_with(
        pkg=PKG,
        path=None,
        flags=None,
        retries=RETRIES,
        sleep=SLEEP,
        build_info=mock_build_info)

  @parameterized.named_parameters(
      ('_googeterror', [[PKG, FLAGS, PATH, RETRIES, SLEEP]]),
      ('_indexerror', [[]]),
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch.object(googet.googet, 'GooGetInstall', autospec=True)
  def test_install_error(self, action_args, mock_install, mock_build_info):
    gi = googet.GooGetInstall(action_args, mock_build_info)
    mock_install.side_effect = googet.googet.GooGetMissingPackageNameError
    with self.assert_raises_with_validation(googet.ActionError):
      gi.Run()

  @parameterized.named_parameters(
      ('_valid_calls', [[PKG, FLAGS, PATH, RETRIES, SLEEP]], None),
      ('_valid_calls_multi', [[PKG, FLAGS, PATH, RETRIES, SLEEP],
                              [PKG, FLAGS, PATH, RETRIES, SLEEP]], None),
  )
  def test_validation_success(self, action_args, build_info):
    g = googet.GooGetInstall(action_args, build_info)
    g.Validate()

  @parameterized.named_parameters(
      ('_list_not_passed', ['String'], None),
      ('_too_few_args', [[]], None),
      ('_too_many_args', [[PKG, FLAGS, PATH, 'abc']], None),
      ('_type_error', [PKG, FLAGS, PATH, RETRIES, SLEEP, 1], None),
  )
  def test_validation_error(self, action_args, build_info):
    g = googet.GooGetInstall(action_args, build_info)
    with self.assert_raises_with_validation(googet.ValidationError):
      g.Validate()


if __name__ == '__main__':
  absltest.main()
