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

"""Constants used by the Glazier imaging code."""

import os
# do not remove: internal placeholder 1

BUILD_LOG_FILE = 'glazier.log'
REG_ROOT = r'SOFTWARE\Glazier'

# Network
DOMAIN = 'domain.example.com'
DOMAIN_DN = 'DC=domain,DC=example,DC=com'
DOMAIN_NAME = 'EXAMPLE'

USER_AGENT = 'Glazier Installer 1.0'

# System
SYS_ROOT = 'C:'
SYS_CACHE = os.path.join(SYS_ROOT, os.sep, 'glazier_cache')
SYS_LOGS_PATH = os.path.join(SYS_ROOT, os.sep, 'Windows', 'Logs', 'Glazier')
SYS_BUILD_LOG = os.path.join(SYS_LOGS_PATH, BUILD_LOG_FILE)
SYS_SYSTEM32 = os.path.join(SYS_ROOT, os.sep, 'Windows', 'System32')
SYS_TASK_LIST = os.path.join(SYS_CACHE, 'task_list.yaml')
SYS_DISM = os.path.join(SYS_SYSTEM32, 'dism.exe')
SYS_PNPUTIL = os.path.join(SYS_SYSTEM32, 'pnputil.exe')
SYS_POWERSHELL = os.path.join(SYS_SYSTEM32, 'WindowsPowerShell', 'v1.0',
                              'powershell.exe')
SYS_GOOGETROOT = os.path.join(SYS_ROOT, os.sep, 'ProgramData', 'GooGet')

# WinPE
WINPE_ROOT = 'X:'
WINPE_CACHE = WINPE_ROOT
WINPE_LOGS_PATH = os.path.join(WINPE_ROOT, os.sep, 'Logs')
WINPE_BUILD_LOG = os.path.join(WINPE_LOGS_PATH, BUILD_LOG_FILE)
WINPE_SYSTEM32 = os.path.join(WINPE_ROOT, os.sep, 'Windows', 'System32')
WINPE_TASK_LIST = os.path.join(WINPE_ROOT, os.sep, 'task_list.yaml')
WINPE_DISM = os.path.join(WINPE_SYSTEM32, 'dism.exe')
WINPE_POWERSHELL = os.path.join(WINPE_SYSTEM32, 'WindowsPowerShell', 'v1.0',
                                'powershell.exe')
WINPE_GOOGETROOT = os.path.join(WINPE_ROOT, os.sep, 'ProgramData', 'GooGet')

# Misc
USB_VOLUME_LABEL = 'BEYONDCORP'
HELP_URI = 'https://glazier-failures.example.com'
USE_REG_64 = True
