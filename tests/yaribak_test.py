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
    cmds = yaribak._get_commands(source_dir, backup_dir)
    self.assertEqual(cmds, [
        f'rsync -aAXHv --delete --progress {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219'
    ])

  def test_nonempty_backupdir(self):
    source_dir = os.path.join(self.tmpdir, 'source')
    backup_dir = os.path.join(self.tmpdir, 'backups')
    os.mkdir(backup_dir)
    os.mkdir(os.path.join(backup_dir, '_backup_20200101_120000'))
    cmds = yaribak._get_commands(source_dir, backup_dir)
    self.assertEqual(cmds, [
        f'cp -al {self.tmpdir}/backups/_backup_20200101_120000 '
        f'{self.tmpdir}/backups/_backup_20220314_235219',
        f'rsync -aAXHv --delete --progress {self.tmpdir}/source/ '
        f'{self.tmpdir}/backups/_backup_20220314_235219'
    ])

  def setUp(self) -> None:
    self.tmpdir_obj = tempfile.TemporaryDirectory(prefix='yaribak_test_')
    self.tmpdir = self.tmpdir_obj.name
    self.patches = []
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
