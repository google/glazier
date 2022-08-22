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

from unittest import mock

from absl.testing import absltest
from glazier.lib import terminator
from glazier.lib import test_utils
from glazier.lib import winpe

from glazier.lib import constants
from glazier.lib import errors

_HELP_MSG = (
    f'See {terminator.constants.SYS_BUILD_LOG} for more info. Need help? Visit '
    f'{terminator.constants.HELP_URI}')

# Define some common Exception instances.
EXCEPTION_1 = Exception('Exception One')
EXCEPTION_2 = ValueError('ValueError Two')
EXCEPTION_3 = ZeroDivisionError('ZeroDivisionError Three')
GLAZIER_ERROR_1 = errors.GlazierError(
    error_code=111, message='GlazierError One')
GLAZIER_ERROR_2 = errors.GlazierError(
    error_code=222, message='GlazierError Two')
GLAZIER_ERROR_3 = errors.GlazierError(
    error_code=333, message='GlazierError Three')
GLAZIER_ERROR_4 = errors.GlazierError(
    error_code=444, message='GlazierError Four')


class LogAndExitTest(test_utils.GlazierTestCase):

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_no_glazier_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception_1 = Exception('Exception One')
    exception_2 = ValueError('ValueError Two')
    exception_3 = ZeroDivisionError('ZeroDivisionError Three')
    raised = test_utils.raise_from(exception_1, exception_2, exception_3)

    with self.assert_raises_with_validation(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), raised)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Glazier encountered the following error\(s\) while imaging..*',
        (r'.*Please consult the troubleshooting links for solutions..*'),
        r'.*1. ZeroDivisionError Three.*',
        fr'.*Troubleshooting: {constants.HELP_URI}#7000.*',
        r'.*Logs from the imaging process can be found at: .+',
        r'.*[*]+.*',
    ]
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_mixed_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception = test_utils.raise_from(EXCEPTION_1, EXCEPTION_2, GLAZIER_ERROR_1,
                                      GLAZIER_ERROR_2)

    with self.assert_raises_with_validation(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), exception)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Glazier encountered the following error\(s\) while imaging..*',
        (r'.*Please consult the troubleshooting links for solutions..*'),
        r'.*1. GlazierError One \(Error Code: 111\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#111.*',
        r'.*2. GlazierError Two \(Error Code: 222\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#222.*',
        r'.*Logs from the imaging process can be found at: .+',
        r'.*[*]+.*',
    ]
    print(critical_msg)
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_all_glazier_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception = test_utils.raise_from(GLAZIER_ERROR_1, GLAZIER_ERROR_2,
                                      GLAZIER_ERROR_3, GLAZIER_ERROR_4)

    with self.assert_raises_with_validation(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), exception)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Glazier encountered the following error\(s\) while imaging..*',
        (r'.*Please consult the troubleshooting links for solutions..*'),
        r'.*1. GlazierError One \(Error Code: 111\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#111.*',
        r'.*2. GlazierError Two \(Error Code: 222\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#222.*',
        r'.*3. GlazierError Three \(Error Code: 333\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#333.*',
        r'.*4. GlazierError Four \(Error Code: 444\).*',
        fr'.*Troubleshooting: {constants.HELP_URI}#444.*',
        r'.*Logs from the imaging process can be found at: .+',
        r'.*[*]+.*',
    ]
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)


if __name__ == '__main__':
  absltest.main()
