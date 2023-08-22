# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Glazier runtime flags."""

from absl import flags
from glazier.lib.spec import spec

BINARY_ROOT_PATH = flags.DEFINE_string(
    'binary_root_path', '/bin', 'Path to the binary storage.'
)
BINARY_SERVER = flags.DEFINE_string(
    'binary_server', '', 'Root URL for binary build files.'
)

CONFIG_BRANCHES = flags.DEFINE_boolean(
    'config_branches', True, 'The configuration repository uses branched paths.'
)
CONFIG_ROOT_PATH = flags.DEFINE_string(
    'config_root_path',
    'config',
    'Path to the root of the configuration directory.',
)
CONFIG_SERVER = flags.DEFINE_string(
    'config_server',
    'https://glazier-server.example.com',
    'Root URL for configuration build data.',
)

GLAZIER_SPEC = flags.DEFINE_enum(
    'glazier_spec',
    'flag',
    list(spec.SPEC_OPTS.keys()),
    (
        'Which host specification module to use for determining host features '
        'like Hostname and OS.'
    ),
)

NTP_SERVER = flags.DEFINE_string(
    'ntp_server',
    'time.google.com',
    'Server to use for synchronizing the local system time.',
)

PRESERVE_TASKS = flags.DEFINE_bool(
    'preserve_tasks', False, 'Preserve the existing task list, if any.'
)

VERIFY_URLS = flags.DEFINE_list(
    'verify_urls',
    [
        'https://dns.google',
    ],
    'Comma-separated list of URLs to verify are reachable at start',
)
