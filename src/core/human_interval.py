# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Basic parser for human intervals.
E.g. parse_to_secs('10 hrs')  # Returns 36000.
"""
import re

from typing import Optional

# String unit to seconds.
# Omit 's' at the end for plural, it is part of the parsing.
_MAPPINGS = {
    'sec': 1,
    'second': 1,
    'min': 60,
    'minute': 60,
    'hr': 60 * 60,
    'hour': 60 * 60,
    'day': 24 * 60 * 60,
    'week': 7 * 24 * 60 * 60,
    'month': 30 * 24 * 60 * 60,
    'year': 365 * 24 * 60 * 60,
}


def parse_to_secs(human_interval: str) -> Optional[int]:
  units = '|'.join(sorted(_MAPPINGS))
  m = re.match(rf'^(?P<value>[0-9]*\.?[0-9]*)\s*(?P<unit>{units})s?$',
               human_interval.lower())
  if not m:
    return None
  return int(m.group('value')) * _MAPPINGS[m.group('unit')]
