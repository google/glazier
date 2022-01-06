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

"""UI for obtaining dynamic configuration settings from the user.

The chooser takes an option file in yaml format which specifies options to
be offered to the user.  The UI is populated dynamically with the options and
various types of form inputs.

The UI automatically times out to prevent it from blocking the build.  If the
user interacts with the UI before the timer expires, the countdown stops and
the user must click to resume the build.  Fields are assigned default values
at startup, and these defaults are also the final values if the UI times out.

When the UI exits, the final state of all the forms is written to the answer
file, to be consumed by the caller.
"""

import logging

# do not remove: internal placeholder 1
from glazier.chooser import fields
from glazier.lib import resources
import tkinter as tk


class Chooser(object):
  """Dynamic UI for user configuration."""

  def __init__(self, options, preload=True):
    self.fields = {}
    self.responses = {}
    self.root = tk.Tk()
    self.row = 0
    if preload:
      self._GuiHeader()
      self._LoadOptions(options)
      self._GuiFooter()

  def _AddExpander(self):
    """Adds an empty Frame which expands vertically in the UI."""
    expander = tk.Frame(self.root)
    expander.grid(column=0, row=self.row)
    self.root.rowconfigure(self.row, weight=1)
    self.row += 1

  def _AddSeparator(self):
    """Adds a Separator visual element (UI decoration)."""
    sep = fields.Separator(self.root)
    sep.grid(column=0, row=self.row, sticky='EW')
    self.root.rowconfigure(self.row, weight=0)
    self.row += 1

  def Display(self):
    """Displays the UI on screen."""
    if self.fields:
      w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
      self.root.geometry('%dx%d+0+0' % (w, h))
      self.root.focus_set()
      self.timer.Countdown()
      self.root.mainloop()
    self._Quit()

  def _GuiFooter(self):
    """Creates all UI elements below the input fields."""
    self._AddExpander()
    self.timer = fields.Timer(self.root)
    self.timer.grid(column=0, row=self.row)
    self.root.bind('<Key>', self.timer.Pause)
    self.root.bind('<Button-1>', self.timer.Pause)
    self.row += 1
    self._AddExpander()
    self._GuiLogo()

  def _GuiHeader(self):
    """Creates all UI elements above the input fields."""
    self.root.columnconfigure(0, weight=1)
    self.root.overrideredirect(1)  # pytype: disable=wrong-arg-types
    top = self.root.winfo_toplevel()
    top.rowconfigure(0, weight=1)
    top.columnconfigure(0, weight=1)

  def _GuiLogo(self):
    """Creates the UI graphical logo."""
    self.logo_frame = tk.Frame(self.root)
    self.logo_frame.columnconfigure(0, weight=1)
    r = resources.Resources()
    path = r.GetResourceFileName('logo.gif')
    self.logo_img = tk.PhotoImage(file=path)
    self.logo = tk.Label(self.logo_frame, image=self.logo_img, text='logo here')
    self.logo.grid(column=0, row=0, sticky='SE')
    self.logo_frame.grid(column=0, row=self.row, sticky='EW')
    self.row += 1

  def _LoadOptions(self, options):
    """Load all options from the options file input.

    UI elements are created for each option

    Args:
      options: a list of all options pending for the user
    """
    for option in options:
      if 'type' not in option:
        logging.error('Untyped option: %s.', option)
        continue
      if option['type'] == 'radio_menu':
        self.fields[option['name']] = fields.RadioMenu(self.root, option)
        self.fields[option['name']].grid(column=0, row=self.row, pady=5)
      elif option['type'] == 'toggle':
        self.fields[option['name']] = fields.Toggle(self.root, option)
        self.fields[option['name']].grid(column=0, row=self.row, pady=5)
      else:
        logging.error('Unknown option type: %s.', option['type'])
        continue
      self.root.rowconfigure(self.row, weight=0)
      self.row += 1
      self._AddSeparator()

  def _Quit(self):
    """Save all responses and exit the UI."""
    for field in self.fields:
      self.responses[field] = self.fields[field].Value()
    self.root.destroy()

  def Responses(self):
    return self.responses
