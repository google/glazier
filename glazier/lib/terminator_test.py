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

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_logs_before_collect(
      self, mock_check_winpe, mock_logging, mock_collect
  ):

    mock_check_winpe.return_value = True
    # Raised and caught here, so log_and_exit runs outside an except block
    # with an exception that carries a traceback.
    raised = test_utils.raise_from(EXCEPTION_1, GLAZIER_ERROR_1)
    self.assertIsNotNone(raised.__traceback__)

    collect_errors = [
        None,
        terminator.logs.LogCollectionError(),
        RuntimeError('unexpected'),
        KeyboardInterrupt(),
    ]
    order = []

    def _record(name, error=None):

      def _side_effect(*unused_args, **unused_kwargs):
        order.append(name)
        if error is not None:
          raise error

      return _side_effect

    mock_logging.debug.side_effect = _record('debug')
    mock_logging.critical.side_effect = _record('critical')
    for collect_error in collect_errors:
      with self.subTest(collect_error=repr(collect_error)):
        order.clear()
        mock_collect.side_effect = _record('collect', collect_error)

        with self.assertRaises(SystemExit) as cm:
          terminator.log_and_exit(terminator.buildinfo.BuildInfo(), raised)

        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(order, ['debug', 'critical', 'collect'])
        traceback_msg = mock_logging.debug.call_args[0][0]
        self.assertIn('Traceback (most recent call last)', traceback_msg)
        self.assertIn('GlazierError One', traceback_msg)
        self.assertIn(
            'IMAGING PROCESS FAILED', mock_logging.critical.call_args[0][0]
        )

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_no_collect(self, mock_check_winpe, mock_logging, mock_collect):

    mock_check_winpe.return_value = True
    with self.assertRaises(SystemExit) as cm:
      terminator.log_and_exit(
          terminator.buildinfo.BuildInfo(), GLAZIER_ERROR_1, collect=False
      )

    self.assertEqual(cm.exception.code, 1)
    mock_collect.assert_not_called()
    self.assertTrue(mock_logging.critical.called)

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_composition_error_still_collects_and_exits(
      self, mock_check_winpe, mock_logging, mock_collect
  ):

    # Fail only the composition call; the later CachePath() call for log
    # collection also checks for WinPE.
    mock_check_winpe.side_effect = [RuntimeError('check_winpe failed'), True]

    with self.assertRaises(SystemExit) as cm:
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), GLAZIER_ERROR_1)

    self.assertEqual(cm.exception.code, 1)
    mock_collect.assert_called_once()
    mock_logging.exception.assert_called_once_with(
        'Failed to compose the detailed failure message.'
    )
    critical_msg = mock_logging.critical.call_args[0][0]
    self.assert_lines_match_patterns(
        critical_msg,
        [
            r'.*IMAGING PROCESS FAILED.*',
            r'.*1\. GlazierError: GlazierError One \(Error Code: 111\).*',
            r'.*[*]+.*',
        ],
    )

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_unprintable_exception_still_collects_and_exits(
      self, mock_check_winpe, mock_logging, mock_collect
  ):

    class UnprintableError(Exception):

      def __str__(self):
        raise RuntimeError('__str__ failed')

    mock_check_winpe.return_value = True

    with self.assertRaises(SystemExit) as cm:
      terminator.log_and_exit(
          terminator.buildinfo.BuildInfo(), UnprintableError()
      )

    self.assertEqual(cm.exception.code, 1)
    mock_collect.assert_called_once()
    mock_logging.exception.assert_called_once_with(
        'Failed to compose the detailed failure message.'
    )
    critical_msg = mock_logging.critical.call_args[0][0]
    self.assert_lines_match_patterns(
        critical_msg.splitlines(),
        [
            r'.*IMAGING PROCESS FAILED.*',
            r'^  1\. UnprintableError$',
            r'.*[*]+.*',
        ],
    )

  def test_exception_summary_unknown_type_name(self):

    class _NamelessMeta(type):

      @property
      def __name__(cls):
        raise RuntimeError('__name__ failed')

    class NamelessError(Exception, metaclass=_NamelessMeta):

      def __str__(self):
        raise RuntimeError('__str__ failed')

    self.assertEqual(
        terminator._exception_summary(NamelessError()), 'Unknown error'
    )

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_unexpected_collect_error_logs_and_exits(
      self, mock_check_winpe, mock_logging, mock_collect
  ):

    mock_check_winpe.return_value = True
    mock_collect.side_effect = RuntimeError('unexpected')

    with self.assertRaises(SystemExit) as cm:
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), GLAZIER_ERROR_1)

    self.assertEqual(cm.exception.code, 1)
    mock_logging.exception.assert_called_once_with(
        'Failed to log the failure or collect logs.'
    )

  @mock.patch.object(terminator.logs, 'Collect', autospec=True)
  @mock.patch.object(terminator, 'logging', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_collect_interrupted_logs_and_exits(
      self, mock_check_winpe, mock_logging, mock_collect
  ):

    mock_check_winpe.return_value = True
    mock_collect.side_effect = KeyboardInterrupt()

    with self.assertRaises(SystemExit) as cm:
      terminator.log_and_exit(terminator.buildinfo.BuildInfo(), GLAZIER_ERROR_1)

    self.assertEqual(cm.exception.code, 1)
    mock_logging.error.assert_called_once_with(
        'Interrupted before exit; logs may not have been collected.'
    )


if __name__ == '__main__':
  absltest.main()
