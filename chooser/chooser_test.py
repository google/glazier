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

from pyfakefs import fake_filesystem
from glazier.chooser import chooser
import mock
from google.apputils import basetest

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


class ChooserTest(basetest.TestCase):

  @mock.patch.object(chooser, 'tk', autospec=True)
  def setUp(self, unused_tk):
    self.ui = chooser.Chooser(_TEST_CONF, preload=False)
    v1 = mock.Mock()
    v1.Value.return_value = 'value1'
    v2 = mock.Mock()
    v2.Value.return_value = 'value2'
    v3 = mock.Mock()
    v3.Value.return_value = 'value3'
    self.ui.fields = {'field1': v1, 'field2': v2, 'field3': v3}

    self.fs = fake_filesystem.FakeFilesystem()
    chooser.resources.os = fake_filesystem.FakeOsModule(self.fs)
    self.fs.CreateFile('/resources/logo.gif')

  @mock.patch.object(chooser.fields, 'Timer', autospec=True)
  def testDislpay(self, timer):
    self.ui.timer = timer.return_value
    self.ui.Display()

  @mock.patch.object(chooser, 'tk', autospec=True)
  @mock.patch.object(chooser.fields, 'Timer', autospec=True)
  def testGuiFooter(self, unused_timer, unused_tk):
    self.ui._GuiFooter()

  def testGuiHeader(self):
    self.ui._GuiHeader()

  @mock.patch.object(chooser.fields, 'RadioMenu', autospec=True)
  @mock.patch.object(chooser.fields, 'Separator', autospec=True)
  @mock.patch.object(chooser.fields, 'Toggle', autospec=True)
  def testLoadOptions(self, toggle, unused_sep, radio):
    self.ui._LoadOptions(_TEST_CONF)
    self.assertEqual(radio.call_args[0][1]['name'], 'system_locale')
    self.assertEqual(toggle.call_args[0][1]['name'], 'puppet_enable')
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

  def testQuit(self):
    self.ui._Quit()
    responses = self.ui.Responses()
    self.assertEqual(responses['field2'], 'value2')
    self.assertEqual(responses['field3'], 'value3')


if __name__ == '__main__':
  basetest.main()
