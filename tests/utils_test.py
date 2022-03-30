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

import pathlib
import unittest
import os
import shutil
import tempfile

from src.core import utils


class TestUtils(unittest.TestCase):

  def test_hardlink_same(self):
    with tempfile.TemporaryDirectory(prefix='yaribak_utils_test_') as tempdir:
      dir1 = pathlib.Path(tempdir) / 'dir1'
      dir2 = pathlib.Path(tempdir) / 'dir2'
      os.makedirs(dir1)
      with open(dir1 / 'file1', 'w') as f:
        f.write('hello 1')
      shutil.copytree(dir1, dir2, copy_function=os.link)
      self.assertTrue(utils.is_hardlinked_replica(dir1, dir2))

  def test_not_hardlinked(self):
    with tempfile.TemporaryDirectory(prefix='yaribak_utils_test_') as tempdir:
      dir1 = pathlib.Path(tempdir) / 'dir1'
      dir2 = pathlib.Path(tempdir) / 'dir2'
      os.makedirs(dir1)
      with open(dir1 / 'file1', 'w') as f:
        f.write('hello 1')
      # Copying, but not hard linking.
      shutil.copytree(dir1, dir2)
      self.assertFalse(utils.is_hardlinked_replica(dir1, dir2))
