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

"""Tests for glazier.lib.actions.tasklist."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import test_utils
from glazier.lib import winpe
from glazier.lib.actions import base
from glazier.lib.actions import tasklist


class TasklistTest(test_utils.GlazierTestCase):

  @mock.patch.object(tasklist, 'logs', autospec=True)
  def setUp(self, logs):
    super().setUp()
    self.tasklist = tasklist.RegenerateTasklist()
    tasklist.logging = logs.logging

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_setup_task_list_host(self, mock_check_winpe):
    tasklist_location = tasklist.constants.SYS_TASK_LIST
    mock_check_winpe.return_value = False
    self.assertEqual(self.tasklist._PurgeTaskList(), tasklist_location)

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_setup_task_list_winpe(self, mock_check_winpe):
    self.patch_constant_file_path(tasklist.constants, 'WINPE_TASK_LIST')
    mock_check_winpe.return_value = True
    tasklist_location = tasklist.constants.WINPE_TASK_LIST
    self.assertEqual(self.tasklist._PurgeTaskList(), tasklist_location)

  @mock.patch.object(tasklist, 'os', autospec=True)
  def test_setup_task_list_error(self, mock_os):
    self.patch_constant_file_path(tasklist.constants, 'SYS_TASK_LIST')
    mock_os.remove.side_effect = OSError
    with self.assertRaises(base.ActionError):
      self.tasklist._PurgeTaskList()


if __name__ == '__main__':
  absltest.main()
