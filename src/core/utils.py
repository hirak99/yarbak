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

import os


def is_hardlinked_replica(dir1: str, dir2: str) -> bool:
  """Returns True if directories have same hard-linked files."""
  for walk1, walk2 in zip(os.walk(dir1), os.walk(dir2)):
    root1, dirs1, files1 = walk1
    root2, dirs2, files2 = walk2
    files1.sort()
    files2.sort()
    if files1 != files2:
      return False
    # With topdown=True (default for os.walk), sorting also ensures that the
    # traversal order is same. Otherwise it technically depends on the file
    # system.
    dirs1.sort()
    dirs2.sort()
    if dirs1 != dirs2:
      return False
    for file1, file2 in zip(files1, files2):
      inode1 = os.lstat(os.path.join(root1, file1)).st_ino
      inode2 = os.lstat(os.path.join(root2, file2)).st_ino
      if inode1 != inode2:
        return False
  return True
