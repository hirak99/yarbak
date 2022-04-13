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

import datetime
import filecmp
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from src.yaribak import backup_processor
from src.yaribak import metadata

from typing import List

# Default expected rsync flags.
_EXPECTED_RSYNC_FLAGS = '-aAXHSv --delete --delete-excluded'


def _dir_compare(dir1: str, dir2: str) -> bool:

  def recursive(cmp: filecmp.dircmp) -> bool:
    if cmp.diff_files or cmp.left_only or cmp.right_only:
      print(f'{cmp.diff_files=}')
      print(f'{cmp.left_only=}')
      print(f'{cmp.right_only=}')
      return False
    for sub_cmp in cmp.subdirs.values():
      if not recursive(sub_cmp):
        return False
    return True

  return recursive(filecmp.dircmp(dir1, dir2))


class TestBackupProcessor(unittest.TestCase):
  _tmpdir: str

  def test_empty_backupdir(self):
    cmds = self._process(self._source_dir, self._backup_dir)
    self.assertEqual(list(cmds), [
        f'mkdir {self._tmpdir}/backups/ysnap__incomplete',
        f'chown {self._user_and_group} {self._tmpdir}/backups/ysnap__incomplete',
        f'[Store metadata at {self._tmpdir}/backups/ysnap__incomplete/backup_context.json]',
        f'rsync {_EXPECTED_RSYNC_FLAGS} {self._tmpdir}/source/ {self._tmpdir}/backups/ysnap__incomplete/payload',
        f'[Rename {self._tmpdir}/backups/ysnap__incomplete to {self._tmpdir}/backups/ysnap_20220314_235219]',
    ])

  def test_excludes(self):
    cmds = self._process(self._source_dir,
                         self._backup_dir,
                         max_to_keep=-1,
                         excludes=['x', 'y'])
    self.assertEqual(list(cmds), [
        f'mkdir {self._tmpdir}/backups/ysnap__incomplete',
        f'chown {self._user_and_group} {self._tmpdir}/backups/ysnap__incomplete',
        f'[Store metadata at {self._tmpdir}/backups/ysnap__incomplete/backup_context.json]',
        f'rsync {_EXPECTED_RSYNC_FLAGS} {self._tmpdir}/source/ {self._tmpdir}/backups/ysnap__incomplete/payload --exclude=x --exclude=y',
        f'[Rename {self._tmpdir}/backups/ysnap__incomplete to {self._tmpdir}/backups/ysnap_20220314_235219]',
    ])

  # Run the functions on an actual directory structure.
  def test_functional(self):
    with open(os.path.join(self._source_dir, 'file1.txt'), 'w') as f:
      f.writelines(['hello 1'])
    with open(os.path.join(self._source_dir, 'file2.txt'), 'w') as f:
      f.writelines(['hello 2'])

    processor = backup_processor.BackupProcessor(dryrun=False,
                                                 verbose=False,
                                                 only_if_changed=True,
                                                 minimum_delay_secs=60)

    # Run.
    processor.process(self._source_dir,
                      self._backup_dir,
                      max_to_keep=5,
                      excludes=[])
    # Compare.
    target_copy_dir = os.path.join(self._backup_dir, 'ysnap_20220314_235219')
    self.assertTrue(
        _dir_compare(self._source_dir, os.path.join(target_copy_dir,
                                                    'payload')))
    # Basic checks on the saved backup_context.
    with open(os.path.join(target_copy_dir, 'backup_context.json')) as f:
      data = metadata.Metadata.fromjson(f.read())
    self.assertEqual(data.source, self._source_dir)

    # Run again.
    self._fake_now = datetime.datetime(2022, 3, 20, 0, 0, 0)
    processor.process(self._source_dir,
                      self._backup_dir,
                      max_to_keep=5,
                      excludes=[])
    # Expect no change (since only_if_changed=True).
    target_copy_dir = os.path.join(self._backup_dir, 'ysnap_20220320_000000')
    self.assertFalse(os.path.isdir(target_copy_dir))

    # Change file structure.
    os.remove(os.path.join(self._source_dir, 'file2.txt'))
    with open(os.path.join(self._source_dir, 'file3.txt'), 'w') as f:
      f.writelines(['hello 3'])
    # Run again, simulating a different time.
    self._fake_now = datetime.datetime(2022, 3, 20, 0, 1, 0)
    target_copy_dir = os.path.join(self._backup_dir, 'ysnap_20220321_000000')
    # Expect no change (since minimum_delay_secs=60).
    self.assertFalse(os.path.isdir(target_copy_dir))
    # Run again, simulating a longer delay.
    self._fake_now = datetime.datetime(2022, 3, 21, 0, 0, 0)
    processor.process(self._source_dir,
                      self._backup_dir,
                      max_to_keep=5,
                      excludes=[])
    # Compare again.
    self.assertTrue(
        _dir_compare(self._source_dir, os.path.join(target_copy_dir,
                                                    'payload')))

  def _process(self, *args, **kwargs_in) -> List[str]:
    processor = backup_processor.BackupProcessor(dryrun=True, verbose=True)
    kwargs = dict(max_to_keep=-1, excludes=[])
    kwargs.update(kwargs_in)
    result = processor._process_iterator(*args, **kwargs)
    return list(result)

  def setUp(self) -> None:
    self._tmpdir_obj = tempfile.TemporaryDirectory(prefix='yaribak_test_')
    self._tmpdir = self._tmpdir_obj.name

    self._source_dir = os.path.join(self._tmpdir, 'source')
    os.mkdir(self._source_dir)
    self._backup_dir = os.path.join(self._tmpdir, 'backups')
    os.mkdir(self._backup_dir)

    # The current user.
    source_path = pathlib.Path(self._source_dir)
    owner, group = source_path.owner(), source_path.group()
    self._user_and_group = f'{owner}:{group}'
    # This is used for all calls to backup_processor, e.g. self._process().
    # May be changed.
    self._fake_now = datetime.datetime(2022, 3, 14, 23, 52, 19)

    self._patches = []
    self._patches.append(
        mock.patch.object(backup_processor,
                          '_now',
                          side_effect=lambda: self._fake_now))
    for p in self._patches:
      p.start()
    return super().setUp()

  def tearDown(self) -> None:
    self._tmpdir_obj.cleanup()
    for p in self._patches:
      p.stop()
    return super().tearDown()
