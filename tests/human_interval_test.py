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

import unittest

from src.yaribak import human_interval


class TestHumanInterval(unittest.TestCase):

  def test_cases(self):
    cases = [
        ('2hr', 7200),
        ('2 h', 7200),
        ('2 hour', 7200),
        ('2  hours', 7200),
        ('.02 h', 72),
        ('2.02 h', 7272),
        ('  2.02  h  ', 7272),
        ('2.2 h x', None),
        ('2 m', 120),
        ('2 M', 5260032),
        ('2 ms', 2e-3),
        ('2 fortenites', None),
        ('2 Ms', None),
    ]
    for input, expected in cases:
      try:
        observed = human_interval.parse_to_secs(input)
      except ValueError:
        observed = None
      if observed is None:
        self.assertIsNone(expected, msg=f'{input} --> {expected!r}')
      else:
        assert expected is not None
        self.assertAlmostEqual(observed,
                               expected,
                               msg=f'{input} --> {expected!r}')
