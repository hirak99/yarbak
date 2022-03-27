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

import json
import unittest
from unittest import mock

from src.core import metadata

from typing import List


class TestMetadata(unittest.TestCase):

  def test_json(self):
    data = metadata.Metadata(source='/path/to/source', epoch=1234)

    json_str = data.asjson()
    json_obj = json.loads(json_str)
    self.assertEqual(json_obj, {
        'source': '/path/to/source',
        'epoch': 1234
    })

    data2 = metadata.Metadata.fromjson(json_str)
    self.assertEqual(data, data2)
