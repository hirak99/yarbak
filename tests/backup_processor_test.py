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

import filecmp
import os
import tempfile
import unittest
from unittest import mock

from src.core import backup_processor
from src.core import metadata

from typing import List, Optional

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
  tmpdir: str

  def test_empty_backupdir(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    cmds = self._process(source_dir, backup_dir)
    self.assertEqual(list(cmds), [
        f'mkdir {self.tmpdir}/backups/_backup_20220314_235219',
        '[Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/backup_context.json]',
        f'rsync {_EXPECTED_RSYNC_FLAGS} {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload',
    ])

  def test_nonempty_backupdir(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    os.mkdir(os.path.join(backup_dir, '_backup_20200101_120000'))
    os.mkdir(os.path.join(backup_dir, '_backup_20200101_120000/payload'))
    cmds = self._process(source_dir, backup_dir)
    self.assertEqual(list(cmds), [
        f'cp -al {self.tmpdir}/backups/_backup_20200101_120000 '
        f'{self.tmpdir}/backups/_backup_20220314_235219',
        '[Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/backup_context.json]',
        f'rsync {_EXPECTED_RSYNC_FLAGS} {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload',
    ])

  def test_excludes(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    cmds = self._process(source_dir,
                         backup_dir,
                         max_to_keep=-1,
                         excludes=['x', 'y'])
    self.assertEqual(list(cmds), [
        f'mkdir {self.tmpdir}/backups/_backup_20220314_235219',
        '[Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/backup_context.json]',
        f'rsync {_EXPECTED_RSYNC_FLAGS} {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload'
        ' --exclude=x --exclude=y',
    ])

  # Create and copy a directory structure.
  def test_functional(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    os.mkdir(source_dir)
    with open(os.path.join(source_dir, 'file1.txt'), 'w') as f:
      f.writelines(['hello 1'])
    with open(os.path.join(source_dir, 'file2.txt'), 'w') as f:
      f.writelines(['hello 2'])

    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    processor = backup_processor.BackupProcessor(dryrun=False, verbose=False)

    # Run.
    processor.process(source_dir, backup_dir, max_to_keep=5, excludes=[])
    # Compare.
    target_copy_dir = os.path.join(backup_dir, '_backup_20220314_235219')
    self.assertTrue(
        _dir_compare(source_dir, os.path.join(target_copy_dir, 'payload')))
    # Basic checks on the saved backup_context.
    with open(os.path.join(target_copy_dir, 'backup_context.json')) as f:
      data = metadata.Metadata.fromjson(f.read())
    self.assertEqual(data.source, source_dir)

    # Change file structure.
    os.remove(os.path.join(source_dir, 'file2.txt'))
    with open(os.path.join(source_dir, 'file3.txt'), 'w') as f:
      f.writelines(['hello 3'])
    # Run again, simulating a different time.
    self.fake_time_str = '20220320_000000'
    processor.process(source_dir, backup_dir, max_to_keep=5, excludes=[])
    target_copy_dir = os.path.join(backup_dir, '_backup_20220320_000000')
    # Compare again.
    self.assertTrue(
        _dir_compare(source_dir, os.path.join(target_copy_dir, 'payload')))

  def _process(self, *args, **kwargs_in) -> List[str]:
    processor = backup_processor.BackupProcessor(dryrun=True, verbose=True)
    kwargs = dict(max_to_keep=-1, excludes=[])
    kwargs.update(kwargs_in)
    result = processor._process_iterator(*args, **kwargs)
    return list(result)

  def setUp(self) -> None:
    self.tmpdir_obj = tempfile.TemporaryDirectory(prefix='yaribak_test_')
    self.tmpdir = self.tmpdir_obj.name
    self.fake_time_str = '20220314_235219'
    self.patches = []
    self.patches.append(
        mock.patch.object(backup_processor,
                          '_times_str',
                          side_effect=lambda: self.fake_time_str))
    for p in self.patches:
      p.start()
    return super().setUp()

  def tearDown(self) -> None:
    self.tmpdir_obj.cleanup()
    for p in self.patches:
      p.stop()
    return super().tearDown()
