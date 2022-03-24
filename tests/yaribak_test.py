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

from more_itertools import side_effect
from src.yaribak import yaribak


class TestYaribak(unittest.TestCase):
  tmpdir: str

  def test_empty_backupdir(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    cmds = yaribak._get_commands(source_dir, backup_dir, **self.default_args)
    self.assertEqual(cmds, [
        f'mkdir {self.tmpdir}/backups/_backup_20220314_235219',
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
    cmds = yaribak._get_commands(source_dir, backup_dir, **self.default_args)
    self.assertEqual(cmds, [
        f'cp -al {self.tmpdir}/backups/_backup_20200101_120000 '
        f'{self.tmpdir}/backups/_backup_20220314_235219',
        f'rsync -aAXHSv {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload '
        '--delete --progress --delete-excluded'
    ])

  def test_excludes(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    cmds = yaribak._get_commands(source_dir,
                                 backup_dir,
                                 max_to_keep=-1,
                                 excludes=['x', 'y'])
    self.assertEqual(cmds, [
        f'mkdir {self.tmpdir}/backups/_backup_20220314_235219',
        f'rsync -aAXHSv {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219/payload '
        '--delete --progress --delete-excluded '
        '--exclude=x --exclude=y'
    ])

  def setUp(self) -> None:
    self.tmpdir_obj = tempfile.TemporaryDirectory(prefix='yaribak_test_')
    self.tmpdir = self.tmpdir_obj.name
    self.patches = []
    self.default_args = dict(max_to_keep=-1, excludes=[])
    self.patches.append(
        mock.patch.object(yaribak,
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
