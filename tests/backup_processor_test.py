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
import tempfile
import unittest
from unittest import mock

from src.core import backup_processor

from typing import List


class TestBackupProcessor(unittest.TestCase):
  tmpdir: str

  def test_empty_backupdir(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    cmds = self._process(source_dir, backup_dir)
    self.assertEqual(list(cmds), [
        f'mkdir {self.tmpdir}/backups/_backup_20220314_235219',
        'Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/metadata.json',
        f'rsync -aAXHSv {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload '
        '--delete --progress --delete-excluded'
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
        'Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/metadata.json',
        f'rsync -aAXHSv {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload '
        '--delete --progress --delete-excluded'
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
        'Store metadata at '
        f'{self.tmpdir}/backups/_backup_20220314_235219/metadata.json',
        f'rsync -aAXHSv {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload '
        '--delete --progress --delete-excluded '
        '--exclude=x --exclude=y'
    ])

  def _process(self, *args, **kwargs_in) -> List[str]:
    processor = backup_processor.BackupProcessor(dryrun=True)
    kwargs = dict(max_to_keep=-1, excludes=[])
    kwargs.update(kwargs_in)
    result = processor._process_iterator(*args, **kwargs)
    return list(result)

  def setUp(self) -> None:
    self.tmpdir_obj = tempfile.TemporaryDirectory(prefix='yaribak_test_')
    self.tmpdir = self.tmpdir_obj.name
    self.patches = []
    self.patches.append(
        mock.patch.object(backup_processor,
                          '_times_str',
                          side_effect=lambda: '20220314_235219'))
    for p in self.patches:
      p.start()
    return super().setUp()

  def tearDown(self) -> None:
    self.tmpdir_obj.cleanup()
    for p in self.patches:
      p.stop()
    return super().tearDown()
