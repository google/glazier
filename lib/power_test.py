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

"""Tests for glazier.lib.power."""

from glazier.lib import power
import mock
from google.apputils import basetest


class PowerTest(basetest.TestCase):

  @mock.patch.object(power.subprocess, 'call', autospec=True)
  def testRestart(self, call):
    power.Restart(60, 'Reboot fixes everything.')
    call.assert_called_with('C:\\Windows\\System32\\shutdown.exe -r -t 60 '
                            '-c "Reboot fixes everything." -f')

  @mock.patch.object(power.subprocess, 'call', autospec=True)
  def testShutdown(self, call):
    power.Shutdown(30, 'Because I said so.')
    call.assert_called_with('C:\\Windows\\System32\\shutdown.exe -s -t 30 '
                            '-c "Because I said so." -f')


if __name__ == '__main__':
  basetest.main()
