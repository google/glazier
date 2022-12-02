# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.flags."""

from absl.testing import absltest
from absl.testing import flagsaver
from glazier.lib import flags
from glazier.lib import test_utils

FLAGS = flags.FLAGS


class FlagTestCase(test_utils.GlazierTestCase):

  def setUp(self):
    super(FlagTestCase, self).setUp()
    flags.ClearCache()


class GetBinaryPathFlagTest(FlagTestCase):

  @flagsaver.flagsaver(
      binary_server='http://whatever/', binary_root_path='/some/path/')
  def test_with_binary_server_flag(self):
    self.assertEqual('http://whatever/some/path/', flags.GetBinaryPathFlag())

  @flagsaver.flagsaver(
      binary_server='',
      config_server='http://something/',
      binary_root_path='/some/path/')
  def test_without_binary_server_flag(self):
    self.assertEqual('http://something/some/path/', flags.GetBinaryPathFlag())


class GetBinaryServerFlagTest(FlagTestCase):

  @flagsaver.flagsaver(binary_server='https://glazier-server.example.com')
  def test_binary_server_from_flag(self):
    self.assertEqual(flags.GetBinaryServerFlag(),
                     'https://glazier-server.example.com')

  def test_binary_server_changes(self):

    r = flags.GetBinaryServerFlag(set_to='https://glazier-server-1.example.com')
    self.assertEqual(r, 'https://glazier-server-1.example.com')

    # remains the same
    self.assertEqual(flags.GetBinaryServerFlag(),
                     'https://glazier-server-1.example.com')

    # changes
    r = flags.GetBinaryServerFlag(
        set_to='https://glazier-server-2.example.com/')
    self.assertEqual(r, 'https://glazier-server-2.example.com')

    # remains the same
    self.assertEqual(flags.GetBinaryServerFlag(),
                     'https://glazier-server-2.example.com')

  @flagsaver.flagsaver(config_server='https://glazier-server-3.example.com')
  def test_binary_server_fallback(self):
    self.assertEqual(flags.GetBinaryServerFlag(),
                     'https://glazier-server-3.example.com')


class GetConfigServerFlagTest(FlagTestCase):

  @flagsaver.flagsaver
  def test_config_server_from_flag(self):
    FLAGS.config_server = 'https://glazier-server.example.com'
    self.assertEqual(flags.GetConfigServerFlag(),
                     'https://glazier-server.example.com')

  def test_config_server_changes(self):

    r = flags.GetConfigServerFlag(set_to='https://glazier-server-1.example.com')
    self.assertEqual(r, 'https://glazier-server-1.example.com')

    # remains the same
    self.assertEqual(flags.GetConfigServerFlag(),
                     'https://glazier-server-1.example.com')

    # changes
    r = flags.GetConfigServerFlag(
        set_to='https://glazier-server-2.example.com/')
    self.assertEqual(r, 'https://glazier-server-2.example.com')

    # remains the same
    self.assertEqual(flags.GetConfigServerFlag(),
                     'https://glazier-server-2.example.com')

  def test_config_server(self):
    return_value = 'https://glazier-server.example.com'
    self.assertEqual(flags.GetConfigServerFlag(), return_value)


if __name__ == '__main__':
  absltest.main()
