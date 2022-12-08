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

"""Tests for glazier.chooser.chooser."""

from unittest import mock

from absl.testing import absltest
from glazier.chooser import chooser

_TEST_CONF = [{
    'name':
        'system_locale',
    'type':
        'radio_menu',
    'prompt':
        'System Locale',
    'options': [
        {
            'label': 'de-de',
            'value': 'de-de',
            'tip': ''
        },
        {
            'label': 'en-gb',
            'value': 'en-gb',
            'tip': ''
        },
        {
            'label': 'en-us',
            'value': 'en-us',
            'tip': '',
            'default': True
        },
        {
            'label': 'es-es',
            'value': 'es-es',
            'tip': ''
        },
        {
            'label': 'fr-fr',
            'value': 'fr-fr',
            'tip': ''
        },
        {
            'label': 'ja-jp',
            'value': 'ja-jp',
            'tip': ''
        },
        {
            'label': 'ko-kr',
            'value': 'ko-kr',
            'tip': ''
        },
        {
            'label': 'zh-cn',
            'value': 'zh-cn',
            'tip': ''
        },
        {
            'label': 'zh-hk',
            'value': 'zh-hk',
            'tip': ''
        },
        {
            'label': 'zh-tw',
            'value': 'zh-tw',
            'tip': ''
        },
    ]
}, {
    'name':
        'puppet_enable',
    'type':
        'toggle',
    'prompt':
        'Enable Puppet',
    'options': [
        {
            'label': 'False',
            'value': False,
            'tip': '',
            'default': True
        },
        {
            'label': 'True',
            'value': True,
            'tip': ''
        },
    ]
}]


class ChooserTest(absltest.TestCase):

  @mock.patch.object(chooser, 'tk', autospec=True)
  def setUp(self, tk):
    super(ChooserTest, self).setUp()
    self.ui = chooser.Chooser(_TEST_CONF, preload=False)
    self.tk = tk
    v1 = mock.Mock()
    v1.Value.return_value = 'value1'
    v2 = mock.Mock()
    v2.Value.return_value = 'value2'
    v3 = mock.Mock()
    v3.Value.return_value = 'value3'
    self.ui.fields = {'field1': v1, 'field2': v2, 'field3': v3}

  @mock.patch.object(chooser.fields, 'Timer', autospec=True)
  def test_display(self, mock_timer):
    self.ui.timer = mock_timer.return_value
    self.ui.Display()

  @mock.patch.object(chooser.fields, 'Timer', autospec=True)
  @mock.patch.object(chooser, 'tk', autospec=True)
  @mock.patch.object(chooser.resources.Resources, 'GetResourceFileName')
  def test_gui_footer(self, mock_getresourcefilename, mock_tk, mock_timer):

    logo_file_path = self.create_tempfile('logo.gif')
    mock_getresourcefilename.return_value = logo_file_path
    self.ui._GuiFooter()

    mock_getresourcefilename.assert_called_with('logo.gif')
    mock_timer.assert_called_with(self.ui.root)
    mock_tk.PhotoImage.assert_called_with(file=logo_file_path)

  def test_gui_header(self):
    self.ui._GuiHeader()

  @mock.patch.object(chooser.fields, 'RadioMenu', autospec=True)
  @mock.patch.object(chooser.fields, 'Separator', autospec=True)
  @mock.patch.object(chooser.fields, 'Toggle', autospec=True)
  def test_load_options(self, mock_toggle, unused_sep, mock_radiomenu):
    self.ui._LoadOptions(_TEST_CONF)
    self.assertEqual(mock_radiomenu.call_args[0][1]['name'], 'system_locale')
    self.assertEqual(mock_toggle.call_args[0][1]['name'], 'puppet_enable')
    # bad options
    self.ui._LoadOptions([{
        'name': 'notype'
    }, {
        'name': 'system_locale',
        'type': 'radio_menu'
    }, {
        'name': 'unknown',
        'type': 'unknown'
    }])

  def test_quit(self):
    self.ui._Quit()
    responses = self.ui.Responses()
    self.assertEqual(responses['field2'], 'value2')
    self.assertEqual(responses['field3'], 'value3')


if __name__ == '__main__':
  absltest.main()
