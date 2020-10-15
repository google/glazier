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

"""Constants and Flags used by the Glazier imaging code."""

from absl import flags

BUILD_LOG_FILE = 'glazier.log'
REG_ROOT = r'SOFTWARE\Glazier'

# Network

DOMAIN = 'domain.example.com'
DOMAIN_DN = 'DC=domain,DC=example,DC=com'
USER_AGENT = 'Glazier Installer 1.0'

# System
SYS_ROOT = 'C:'
SYS_CACHE = '%s\\glazier_cache' % SYS_ROOT
SYS_LOGS_PATH = '%s\\Windows\\Logs\\Glazier' % SYS_ROOT
SYS_BUILD_LOG = '%s\\%s' % (SYS_LOGS_PATH, BUILD_LOG_FILE)
SYS_SYSTEM32 = '%s\\Windows\\System32' % SYS_ROOT
SYS_TASK_LIST = '%s\\task_list.yaml' % SYS_CACHE
SYS_POWERSHELL = '%s\\WindowsPowerShell\\v1.0\\powershell.exe' % SYS_SYSTEM32
SYS_GOOGETROOT = '%s\\ProgramData\\GooGet' % SYS_ROOT

# WinPE
WINPE_ROOT = 'X:'
WINPE_CACHE = WINPE_ROOT
WINPE_LOGS_PATH = '%s\\Logs' % WINPE_ROOT
WINPE_BUILD_LOG = '%s\\%s' % (WINPE_LOGS_PATH, BUILD_LOG_FILE)
WINPE_SYSTEM32 = '%s\\Windows\\System32' % WINPE_ROOT
WINPE_TASK_LIST = '%s\\task_list.yaml' % WINPE_ROOT
WINPE_DISM = '%s\\dism.exe' % WINPE_SYSTEM32
WINPE_POWERSHELL = ('%s\\WindowsPowerShell\\v1.0\\powershell.exe' %
                    WINPE_SYSTEM32)
WINPE_GOOGETROOT = '%s\\ProgramData\\GooGet' % WINPE_ROOT

USB_VOLUME_LABEL = 'BEYONDCORP'

USE_REG_64 = True

## Flags

FLAGS = flags.FLAGS
flags.DEFINE_string('binary_root_path', '/bin', 'Path to the binary storage.')
flags.DEFINE_string('binary_server', '', 'Root URL for binary build files.')
flags.DEFINE_boolean('config_branches', True,
                     'The configuration repository uses branched paths.')
flags.DEFINE_string('config_root_path', '',
                    'Path to the root of the configuration directory.')
flags.DEFINE_string('config_server', 'https://glazier-server.example.com',
                    'Root URL for configuration build data.')

flags.DEFINE_enum('environment', 'Host', ['Host', 'WinPE'],
                  'The running host environment.')
flags.DEFINE_string('ntp_server', 'time.google.com',
                    'Server to use for synchronizing the local system time.')
flags.DEFINE_list(
    'verify_urls',
    [
        'https://www.catalog.update.microsoft.com/Home.aspx',
    ],
    'Comma-separated list of URLs to verify are reachable at start')
