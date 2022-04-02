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

import dataclasses
import json

from typing import Optional


@dataclasses.dataclass
class Metadata:
  source: str
  # Time when the backup was created.
  epoch: int
  # Present if the backup was updated when called with only-if-changed.
  updated_epoch: Optional[int] = None

  def asjson(self) -> str:
    return json.dumps(dataclasses.asdict(self), indent=True, sort_keys=True)

  @staticmethod
  def fromjson(json_str: str) -> 'Metadata':
    return Metadata(**json.loads(json_str))

  def save_to(self, fname: str) -> None:
    with open(fname, 'w') as f:
      f.write(self.asjson())

  @staticmethod
  def load_from(fname: str) -> 'Metadata':
    with open(fname) as f:
      return Metadata.fromjson(f.read())
