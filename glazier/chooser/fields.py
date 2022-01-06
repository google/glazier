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

"""Form fields available for display in the chooser UI.

The chooser UI displays a dynamic series of fields to the user.  In order to
cope with a variable quantity of fields, each set of options is enclosed
in a Frame, with Frames stacked in a single column in the top level.

Each Frame type that accepts user input is expected to offer a public Value
function which will return the state of the field in a yaml-compatible format.
This is called at the UI exit for final response storage.
"""
# do not remove: internal placeholder 1

import tkinter as tk


class RadioMenu(tk.Frame):
  """Radio menu provides a dropdown menu containing radio buttons.

  One and only one menu element can be selected from the list.
  """

  def __init__(self, root, option):
    tk.Frame.__init__(self, root)
    self.label = tk.Label(self, text=option['prompt'])
    self.label.grid(row=0, column=0, padx=20)
    self.button = tk.Menubutton(self, text='Choose One', relief=tk.GROOVE)
    self.menu = tk.Menu(self.button)
    self.button['menu'] = self.menu
    self.select = tk.StringVar()
    for opt in option['options']:
      self.menu.add_radiobutton(label=opt['label'], variable=self.select,
                                value=opt['value'], command=self._Update)
      if 'default' in opt:
        self.select.set(opt['value'])
        self._Update()

    self.button.grid(row=0, column=1)

  def _Update(self):
    current = self.Value()
    self.button.configure(text=current)

  def Value(self):
    return self.select.get()


class Separator(tk.Frame):
  """A decorative separator."""

  def __init__(self, root):
    tk.Frame.__init__(self, root, height=2, bd=1, relief=tk.SUNKEN)


class Label(tk.Frame):
  """A text label."""

  def __init__(self, root, text, font_name='Helvetica', font_size=16):
    tk.Frame.__init__(self, root)
    self.label = tk.Label(self, text=text, font=font_name, font_size=font_size)  # pytype: disable=wrong-keyword-args
    self.label.grid(row=0, column=0, padx=20)


class Timer(tk.Frame):
  """Countdown timer with Image Now button for UI footer."""

  def __init__(self, root, timeout=60):
    tk.Frame.__init__(self, root)
    self.callback_id = None
    self.root = root
    self._counter = timeout
    self.countdown_1 = tk.Label(self, text='Build will start in...',
                                font=('Helvetica', 16))
    self.countdown_2 = tk.Label(self, text=self._counter,
                                font=('Helvetica', 16))
    self.countdown_3 = tk.Label(self, text='... or ...')
    self.image_now = tk.Button(self, text='Image Now', command=self._Quit,
                               font=('Helvetica', 18))
    self.countdown_1.grid(row=0, column=0)
    self.countdown_2.grid(row=0, column=1)
    self.countdown_3.grid(row=0, column=2)
    self.image_now.grid(row=0, column=3)

  def Pause(self, event):
    self.countdown_1.configure(text='Automatic build paused...')
    self.countdown_2.configure(text='')
    self.countdown_3.configure(text='')
    self._counter = -1

  def Countdown(self):
    if self._counter < 0:  # user interrupt
      return
    if self._counter == 0:  # timeout
      self._Quit()
    self._counter -= 1
    self.countdown_2.configure(text=self._counter)
    self.callback_id = self.root.after(1000, self.Countdown)

  def _Quit(self):
    self.root.after_cancel(self.callback_id)
    self.root.quit()


class Toggle(tk.Frame):
  """An set of radio buttons with On (True)/Off (False) values."""

  def __init__(self, root, option):
    tk.Frame.__init__(self, root)
    self.label = tk.Label(self, text=option['prompt'])
    self.label.grid(row=0, column=0, padx=20)

    self.state = tk.BooleanVar()
    self.on_button = tk.Radiobutton(self, text='On', variable=self.state,
                                    value=True)
    self.off_button = tk.Radiobutton(self, text='Off', variable=self.state,
                                     value=False)
    for opt in option['options']:
      if 'default' in opt:
        self.state.set(opt['value'])

    self.on_button.grid(row=0, column=1)
    self.off_button.grid(row=0, column=2)

  def Value(self):
    return self.state.get()
