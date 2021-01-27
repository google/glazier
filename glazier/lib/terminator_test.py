# Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.terminator."""


from absl.testing import absltest
from glazier.lib import terminator
from glazier.lib import winpe
import mock

_HELP_MSG = (
    f'See {terminator.constants.SYS_BUILD_LOG} for more info. Need help? Visit '
    f'{terminator.constants.HELP_URI}')


class TerminatorTest(absltest.TestCase):

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_log_and_exit_(self, wpe, log):
    wpe.return_value = True
    with self.assertRaises(SystemExit):
      terminator.log_and_exit('image failed', terminator.buildinfo.BuildInfo())
    log.fatal.assert_called_with(
        f'image failed\n\nSee {terminator.constants.WINPE_BUILD_LOG} for more '
        f'info. Need help? Visit {terminator.constants.HELP_URI}#4000')
    self.assertTrue(log.debug.called)

  @mock.patch.object(terminator, 'logging', autospec=True)
  def test_log_and_exit_code(self, log):
    with self.assertRaises(SystemExit):
      terminator.log_and_exit('image failed', terminator.buildinfo.BuildInfo(),
                              1234, False)
    log.fatal.assert_called_with(f'image failed\n\n{_HELP_MSG}#1234')

  @mock.patch.object(terminator, 'logging', autospec=True)
  def test_log_and_exit_exception(self, log):
    with self.assertRaises(SystemExit):
      terminator.log_and_exit(
          'image failed',
          terminator.buildinfo.BuildInfo(),
          exception=Exception('FakeException'),
          collect=False)
    log.fatal.assert_called_with(
        f'image failed\n\nException] FakeException\n\n'
        f'{_HELP_MSG}#4000')

if __name__ == '__main__':
  absltest.main()
