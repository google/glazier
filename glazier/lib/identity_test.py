# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.identity."""

from unittest import mock

from absl.testing import absltest

from glazier.lib import identity

from glazier.lib import constants
from glazier.lib import errors

USERNAME = 'bert'
HOSTNAME = 'earnie-pc'


class RegUtilTest(absltest.TestCase):

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  def test_get_username(self, gv):
    gv.return_value = USERNAME
    self.assertEqual(identity.get_username(), USERNAME)

  @mock.patch.object(identity.interact, 'GetUsername', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_domain(self, sv, prompt):
    prompt.return_value = USERNAME
    self.assertEqual(identity.set_username(prompt='domain join'), USERNAME)
    prompt.assert_called_with('domain join')
    sv.assert_called_with('Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.interact, 'GetUsername', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_none(self, sv, prompt):
    prompt.return_value = USERNAME
    self.assertEqual(identity.set_username(), USERNAME)
    sv.assert_called_with('Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username(self, sv):
    self.assertEqual(identity.set_username(USERNAME), USERNAME)
    sv.assert_called_with('Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_error(self, sv):
    sv.side_effect = errors.RegistrySetError
    self.assertRaises(errors.RegistrySetError, identity.set_username, USERNAME)

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  def test_get_hostname(self, gv):
    gv.return_value = HOSTNAME
    self.assertEqual(identity.get_hostname(), HOSTNAME)

  @mock.patch.object(identity.socket, 'gethostname', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname_none(self, sv, gh):
    gh.return_value = HOSTNAME
    self.assertEqual(identity.set_hostname(), HOSTNAME)
    sv.assert_called_with('Name', HOSTNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname(self, sv):
    self.assertEqual(identity.set_hostname(HOSTNAME), HOSTNAME)
    sv.assert_called_with('Name', HOSTNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname_error(self, sv):
    sv.side_effect = errors.RegistrySetError
    self.assertRaises(errors.RegistrySetError, identity.set_hostname)


if __name__ == '__main__':
  absltest.main()
