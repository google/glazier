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

from glazier.lib.actions import abort
import mock
from google.apputils import basetest


class AbortTest(basetest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testAbort(self, build_info):
    ab = abort.Abort(['abort message'], build_info)
    self.assertRaises(abort.ActionError, ab.Run)

  def testAbortValidate(self):
    ab = abort.Abort('abort message', None)
    self.assertRaises(abort.ValidationError, ab.Validate)
    ab = abort.Abort([1, 2, 3], None)
    self.assertRaises(abort.ValidationError, ab.Validate)
    ab = abort.Abort([1], None)
    self.assertRaises(abort.ValidationError, ab.Validate)
    ab = abort.Abort(['Error Message'], None)
    ab.Validate()

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  @mock.patch('glazier.lib.interact.Prompt', autospec=True)
  def testWarn(self, prompt, build_info):
    warn = abort.Warn(['warning message'], build_info)
    prompt.return_value = None
    self.assertRaises(abort.ActionError, warn.Run)
    prompt.return_value = 'no thanks'
    self.assertRaises(abort.ActionError, warn.Run)
    prompt.return_value = 'Y'
    warn.Run()

  def testWarnValidate(self):
    warn = abort.Warn('abort message', None)
    self.assertRaises(abort.ValidationError, warn.Validate)
    warn = abort.Warn([1, 2, 3], None)
    self.assertRaises(abort.ValidationError, warn.Validate)
    warn = abort.Warn([1], None)
    self.assertRaises(abort.ValidationError, warn.Validate)
    warn = abort.Warn(['Error Message'], None)
    warn.Validate()


if __name__ == '__main__':
  basetest.main()
