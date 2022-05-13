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

USERNAME = 'bert'
HOSTNAME = 'earnie-pc'


class IdentityTest(absltest.TestCase):

  def setUp(self):
    super(IdentityTest, self).setUp()
    identity.get_username.cache_clear()
    identity.get_hostname.cache_clear()

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  def test_get_username_success(self, mock_get_value):
    mock_get_value.return_value = USERNAME
    self.assertEqual(identity.get_username(), USERNAME)

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  @mock.patch.object(identity.logging, 'error', autospec=True)
  def test_get_username_error(self, mock_error, mock_get_value):
    mock_get_value.side_effect = identity.registry.Error
    identity.get_username()
    self.assertTrue(mock_error.called)

  @mock.patch.object(identity.interact, 'GetUsername', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_domain(self, mock_set_value, mock_get_username):
    mock_get_username.return_value = USERNAME
    self.assertEqual(identity.set_username(prompt='domain join'), USERNAME)
    mock_get_username.assert_called_with('domain join')
    mock_set_value.assert_called_with(
        'Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.interact, 'GetUsername', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_none(self, mock_set_value, mock_get_username):
    mock_get_username.return_value = USERNAME
    self.assertEqual(identity.set_username(), USERNAME)
    mock_set_value.assert_called_with(
        'Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_success(self, mock_set_value):
    self.assertEqual(identity.set_username(USERNAME), USERNAME)
    mock_set_value.assert_called_with(
        'Username', USERNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_username_error(self, mock_set_value):
    mock_set_value.side_effect = identity.registry.Error
    self.assertRaises(identity.Error, identity.set_username, USERNAME)

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  def test_get_hostname_success(self, mock_get_value):
    mock_get_value.return_value = HOSTNAME
    self.assertEqual(identity.get_hostname(), HOSTNAME)

  @mock.patch.object(identity.registry, 'get_value', autospec=True)
  @mock.patch.object(identity.logging, 'error', autospec=True)
  def test_get_hostname_error(self, mock_error, mock_get_value):
    mock_get_value.side_effect = identity.registry.Error
    identity.get_hostname()
    self.assertTrue(mock_error.called)

  @mock.patch.object(identity.socket, 'gethostname', autospec=True)
  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname_none(self, mock_set_value, mock_gethostname):
    mock_gethostname.return_value = HOSTNAME
    self.assertEqual(identity.set_hostname(), HOSTNAME)
    mock_set_value.assert_called_with(
        'Name', HOSTNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname_success(self, mock_set_value):
    self.assertEqual(identity.set_hostname(HOSTNAME), HOSTNAME)
    mock_set_value.assert_called_with(
        'Name', HOSTNAME, path=constants.REG_ROOT)

  @mock.patch.object(identity.registry, 'set_value', autospec=True)
  def test_set_hostname_error(self, mock_set_value):
    mock_set_value.side_effect = identity.registry.Error
    self.assertRaises(identity.Error, identity.set_hostname)


if __name__ == '__main__':
  absltest.main()
