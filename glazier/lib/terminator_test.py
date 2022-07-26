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
from absl.testing import parameterized
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


class GetCausalChainTest(parameterized.TestCase):

  def test_missing_argument(self):
    with self.assertRaises(ValueError):
      terminator._get_causal_chain(None)

  def test_single_exception(self):
    exception = ZeroDivisionError('some error')
    expected = [exception]
    actual = terminator._get_causal_chain(exception)
    self.assertEqual(expected, actual)

  def test_success(self):

    # Create a ZeroDivisionError with some history.
    expected = [
        Exception('root'),
        ValueError('intermediate'),
        ZeroDivisionError('final')
    ]
    exception = test_utils.raise_from(*expected)
    self.assertIsInstance(exception, ZeroDivisionError)

    actual = terminator._get_causal_chain(exception)
    self.assertEqual(expected, actual)


class GetRootCauseExceptionTest(parameterized.TestCase):

  def test_missing_argument(self):
    with self.assertRaises(ValueError):
      terminator._get_root_cause_exception(None)

  @parameterized.named_parameters(
      ('_single_exception', [EXCEPTION_1], EXCEPTION_1),
      ('_single_glazier_error', [GLAZIER_ERROR_1], GLAZIER_ERROR_1),
      ('_mixed_errors', [
          EXCEPTION_1, EXCEPTION_2, GLAZIER_ERROR_3, GLAZIER_ERROR_4
      ], GLAZIER_ERROR_3),
      ('_all_glazier_errors', [
          GLAZIER_ERROR_1, GLAZIER_ERROR_2, GLAZIER_ERROR_3, GLAZIER_ERROR_4
      ], GLAZIER_ERROR_1),
      ('_no_glazier_errors', [EXCEPTION_1, EXCEPTION_2, EXCEPTION_3
                             ], EXCEPTION_1),
  )
  def test_get(self, exception, expected):
    actual = terminator._get_root_cause_exception(exception)
    self.assertEqual(expected, actual)


class LogAndExitTest(test_utils.GlazierTestCase):

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_no_glazier_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception = test_utils.raise_from(EXCEPTION_1, EXCEPTION_2, EXCEPTION_3)

    with self.assertRaises(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), exception)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Root Cause: Exception One.*',
        r'.*Location: test_utils.py:[0-9]+.*',
        r'.*Logs: .+',
        fr'.*Troubleshooting: {constants.HELP_URI}#7000.*',
    ]
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_mixed_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception = test_utils.raise_from(EXCEPTION_1, EXCEPTION_2, GLAZIER_ERROR_1,
                                      GLAZIER_ERROR_2)

    with self.assertRaises(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), exception)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Root Cause: GlazierError One \(Error Code: 111\).*',
        r'.*Location: test_utils.py:[0-9]+.*',
        r'.*Logs: .+',
        fr'.*Troubleshooting: {constants.HELP_URI}#111.*',
    ]
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)

  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_all_glazier_errors(self, mock_check_winpe, mock_logging):

    mock_check_winpe.return_value = True
    exception = test_utils.raise_from(GLAZIER_ERROR_1, GLAZIER_ERROR_2,
                                      GLAZIER_ERROR_3, GLAZIER_ERROR_4)

    with self.assertRaises(SystemExit):
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), exception)

    # Extract the logging.critical() message and split it up by newlines.
    critical_msg = mock_logging.critical.call_args[0][0]

    # Verify that there's a line matching each of the given regexes.
    patterns = [
        r'.*IMAGING PROCESS FAILED.*',
        r'.*Root Cause: GlazierError One \(Error Code: 111\).*',
        r'.*Location: test_utils.py:[0-9]+.*',
        r'.*Logs: .+',
        fr'.*Troubleshooting: {constants.HELP_URI}#111.*',
    ]
    self.assert_lines_match_patterns(critical_msg.splitlines(), patterns)


if __name__ == '__main__':
  absltest.main()
