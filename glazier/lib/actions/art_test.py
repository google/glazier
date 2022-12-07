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

"""Tests for glazier.lib.actions.art."""
from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib.actions import art

_TEST_CONTENT = r"""
  / ____| |         (_)
 | |  __| | __ _ _____  ___ _ __
 | | |_ | |/ _` |_  / |/ _ \ '__|
 | |__| | | (_| |/ /| |  __/ |
  \_____|_|\__,_/___|_|\___|_|   """


class PrintFromFileTest(parameterized.TestCase):

  def setUp(self):

    super(PrintFromFileTest, self).setUp()
    self.test_path = self.create_tempfile(
        file_path='test.ascii', content=_TEST_CONTENT).full_path

  @mock.patch('builtins.print', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_print_from_file(self, mock_buildinfo, mock_print):
    art.PrintFromFile([self.test_path], mock_buildinfo).Run()
    mock_print.assert_called_once_with(_TEST_CONTENT)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_print_from_file_not_exist_error(self, mock_buildinfo):
    with self.assertRaises(art.FileNotFound):
      art.PrintFromFile(['/some_fake_path'], mock_buildinfo).Run()

  @mock.patch('builtins.print', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_print_from_file_not_exist_pass(self, mock_buildinfo, mock_print):
    art.PrintFromFile(['/some_fake_path', True], mock_buildinfo).Run()
    self.assertFalse(mock_print.called)

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_get_content(self, mock_buildinfo):
    content = art.PrintFromFile._get_content(mock_buildinfo, self.test_path)
    self.assertEqual(content, _TEST_CONTENT)

  @parameterized.named_parameters(
      ('_not_a_list', 'interactive', None),
      ('_invalid_list_member_types', [1, 2, 3], None),
      ('_list_too_short', [], None),
  )
  def test_print_from_file_validation_failure(self, print_args, build_info):
    pff = art.PrintFromFile(print_args, build_info)
    with self.assertRaises(art.ValidationError):
      pff.Validate()

  def test_print_from_file_validation_success(self):
    pff = art.PrintFromFile([self.test_path], None)
    pff.Validate()


if __name__ == '__main__':
  absltest.main()
