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
"""Tests for glazier.lib.actions.tpm."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import bitlocker
from glazier.lib import test_utils
from glazier.lib.actions import tpm


class TpmTest(test_utils.GlazierTestCase):

  @mock.patch.object(tpm.bitlocker, 'Bitlocker', autospec=True)
  def test_bitlocker_enable(self, mock_bitlocker):
    b = tpm.BitlockerEnable(['ps_tpm'], None)
    b.Run()
    mock_bitlocker.assert_called_with('ps_tpm')
    self.assertTrue(mock_bitlocker.return_value.Enable.called)
    side_effect = bitlocker.BitlockerActivationFailedError()
    mock_bitlocker.return_value.Enable.side_effect = side_effect
    with self.assert_raises_with_validation(tpm.ActionError):
      b.Run()

  @parameterized.named_parameters(
      ('_wrong_arg_type', 30, None),
      ('_arg_list_too_short', [], None),
      ('_unsupported_mode', ['invalid'], None),
      ('_arg_list_too_long', ['ps_tpm', 'ps_tpm'], None),
  )
  def test_bitlocker_enable_failure(self, enable_args, build_info):
    b = tpm.BitlockerEnable(enable_args, build_info)
    with self.assert_raises_with_validation(tpm.ValidationError):
      b.Validate()

  def test_bitlocker_enable_success(self):
    b = tpm.BitlockerEnable(['ps_tpm'], None)
    b.Validate()


if __name__ == '__main__':
  absltest.main()
