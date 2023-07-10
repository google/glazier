# Copyright 2023 Google Inc. All Rights Reserved.
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

"""OS Selector for glazier that reads config from file."""

import re

from absl import flags
from glazier.lib import interact
from glazier.lib import powershell
from glazier.lib.config import files

from glazier.lib import constants
from glazier.lib import errors

_OS_SELECTOR_CONFIG = flags.DEFINE_string('os_selector_config', '',
                                          'Yaml file for OS selection menu')


class Error(errors.GlazierError):
  pass


class UnsupportedModelError(Error):

  def __init__(self, model: str):
    super().__init__(
        error_code=errors.ErrorCode.UNSUPPORTED_MODEL,
        message=f'System OS/model does not have imaging support: {model}')


class OSSelector(object):
  """Creates a menu based on os_selector_config."""

  def __init__(self):
    self.config = files.Read('{0}/{1}'.format(constants.CONFIG_SERVER.value,
                                              _OS_SELECTOR_CONFIG.value))
    self.model = ''

  def _OSCode(self):
    """Determines the OS code from flag or config file.

    Returns:
      os_code: The determined os version to run.

    Raises:c
      UnsupportedModelError
    """
    try:
      os_code = self.config['os'][0][1][0]  # pytype: disable=unsupported-operands  # always-use-return-annotations
    except IndexError as e:
      raise UnsupportedModelError(self.model) from e
    return os_code

  def AutoOrManual(self, computermodel):
    """Determines whether or not to show menu for selection."""
    self.model = computermodel
    self._TrimOSConfig()
    os_code = self._OSCode()
    timeout = 15
    result = interact.Keystroke(
        ('Press any key to bring up OS Selection menu. Imaging will '
         'begin in {0} seconds.\n\n'
         'The default OS selected is {1}'.format(timeout, os_code)),
        timeout=timeout)
    if result:
      os_code = self._GetResponse()

    return os_code

  def _ShowMenu(self):
    """Display the menu and return the regex of allowed responses."""

    # Advanced Menu
    print('\nAdvanced options:')
    print('P. Start PowerShell')

    choices = 'pe'
    # OS Selection Menu
    print('\nPlease select the Windows OS to install:')
    for os in self.config['os']:  # pytype: disable=unsupported-operands  # always-use-return-annotations
      num = self.config['os'].index(os)  # pytype: disable=unsupported-operands  # always-use-return-annotations
      printstring = self._PrintOSOption(os, num)
      if printstring:
        print(printstring)
      choices += str(num + 1)
    return '^[{}]$'.format(choices)

  def _TrimOSConfig(self):
    """Helper method to trim the OS selection menu."""
    config = []
    for os in self.config['os']:  # pytype: disable=unsupported-operands  # always-use-return-annotations
      if self._IsModelAllowed(os):
        config += [os]
    self.config['os'] = config  # pytype: disable=unsupported-operands  # always-use-return-annotations

  def _PrintOSOption(self, os, num):
    if not os[3]:
      return '{0}. {1}'.format(num + 1, os[0])
    return ''

  def _IsModelAllowed(self, os):
    """Method to determine if OS is allowed on system."""
    allowed = False
    if not os[2]:
      allowed = True
    for restrict_by_model in os[2]:
      if restrict_by_model[:1] == '!':
        if restrict_by_model[1:-1] in self.model:
          return False
        else:
          allowed = True
      if restrict_by_model in self.model:
        allowed = True
    return allowed

  def _GetResponse(self):
    """Obtain and evaluate user input."""
    valid_responses = self._ShowMenu()
    response = ''
    answer_track = 1
    while not re.match(valid_responses, response):
      print('')
      response = input('Select from choices: ').lower()
    if response == 'p':
      _StartPs()
    else:
      answer_os = int(response) - 1
      answer_track = self._TrackMenu(self.config['os'][answer_os])  # pytype: disable=unsupported-operands  # always-use-return-annotations
    return self.config['os'][answer_os][1][answer_track]  # pytype: disable=unsupported-operands  # always-use-return-annotations

  def _TrackMenu(self, os):
    """Display track selection menu."""
    answer_track = ''
    tracks = ''
    track_count = 0
    print('\nPlease select a track for the installation of {}'.format(os[0]))

    for track in os[1]:
      track_count += 1
      if track:
        tracks += str(track_count)
        if track_count == 1:
          print('1. Stable')
        elif track_count == 2:
          print('2. Testing')
        elif track_count == 3:
          print('3. Unstable')
        else:
          print('{0}. {1}'.format(track_count, track))

    answer_track_re = ('^[{}]$'.format(tracks))
    while not re.match(answer_track_re, answer_track):
      print('')
      answer_track = input('Track Choice: ')
    return int(answer_track) - 1


def _StripMargin(message, deliminator='|'):
  """Function to strip the margins from multiline strings.

  Equivalent to the stripMargin function in scala:
  https://www.oreilly.com/library/view/scala-cookbook/9781449340292/ch01s03.html

  Args:
    message: message to strip margins from
    deliminator: character to mark the start of a margin (default pipe '|')

  Returns:
    stripped string
  """
  return re.sub(
      pattern=fr'^[ \t]+{re.escape(deliminator)}',
      repl='',
      string=message,
      flags=re.MULTILINE)


def _StartPs():
  """Open a PowerShell command shell."""
  ps = powershell.PowerShell()
  ps.StartShell()
