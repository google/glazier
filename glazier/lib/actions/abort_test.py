# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.actions.abort."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized

from glazier.lib import test_utils
from glazier.lib.actions import abort


class AbortTest(test_utils.GlazierTestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_abort(self, mock_buildinfo):
    ab = abort.Abort(['abort message'], mock_buildinfo)
    with self.assert_raises_with_validation(abort.ActionError):
      ab.Run()

  @parameterized.named_parameters(
      ('_invalid_argument_type_str', 'abort message', None),
      ('_invalid_args_length', [1, 2, 3], None),
      ('_invalid_argument_type_int', [1], None),
  )
  def test_abort_validation_error(self, action_args, build_info):
    ab = abort.Abort(action_args, build_info)
    with self.assert_raises_with_validation(abort.ValidationError):
      ab.Validate()

  def test_abort_validation_success(self):
    ab = abort.Abort(['Error Message'], None)
    ab.Validate()

  @parameterized.named_parameters(
      ('_none', None),
      ('_invalid_response', 'no thanks'),
  )
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch('glazier.lib.interact.Prompt', autospec=True)
  def test_warn_action_error(self, prompt_return_value, mock_prompt,
                             mock_buildinfo):
    warn = abort.Warn(['warning message'], mock_buildinfo)
    mock_prompt.return_value = prompt_return_value
    with self.assert_raises_with_validation(abort.ActionError):
      warn.Run()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch('glazier.lib.interact.Prompt', autospec=True)
  def test_warn_action_success(self, mock_prompt, mock_buildinfo):
    warn = abort.Warn(['warning message'], mock_buildinfo)
    mock_prompt.return_value = 'Y'
    warn.Run()

  @parameterized.named_parameters(
      ('_invalid_argument_type_str', 'abort message', None),
      ('_invalid_args_length', [1, 2, 3], None),
      ('_invalid_argument_type_int', [1], None),
  )
  def test_warn_validation_error(self, action_args, build_info):
    warn = abort.Warn(action_args, build_info)
    with self.assert_raises_with_validation(abort.ValidationError):
      warn.Validate()

  def test_warn_validation_success(self):
    warn = abort.Warn(['Error Message'], None)
    warn.Validate()


if __name__ == '__main__':
  absltest.main()
