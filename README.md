Yet another rsync based incremental backup utility.

# Purpose

An utility to maintain incremental backups in differnet directories.

The backups in each directory will contain entire image, but the incremental
nature comes from the fact that unchanged files will be hard linked sharing the
same space across backups.

# Quick Start

```bash
# Install.
sudo pip3 install yaribak

# Make a directory for backups.
mkdir -p /path/to/abc_backups

# Create a new backup in a subdir of destination.
yaribak /path/to/abc /path/to/abc_backups

# Now you can run the last line again to update the backup.
# Each time you do that -
# 1) Previous backups will be preserved.
# 2) The new backup will be created in a subdirectory.
# 3) Only changed files will take up space.
```

# Setup and Invocation

## Option 1: pip

This is the recommend way to install for general purpose usage.

```bash
# Installation.
sudo pip3 install yaribak

# Invoke.
yaribak --help
```

You can leave out the `sudo` in most distributions, or if you don't want to
backup with super-user privileges.

You may uninstall with `sudo pip uninstall yaribak`.

## Option 2: Install from git repo

This option builds and installs it locally from the repo.

```bash
# Clone repository.
mkdir -p /path/to/git
git clone https://github.com/hirak99/yaribak

# Install python build.
python3 -m pip install --upgrade build

# Install yaribak.
/path/to/git/scripts/rebuild_install_locally.sh

# Invoke.
yaribak --help
```

After installation, you can `rm -r` the repo if you no longer need it.

You may uninstall with `pip uninstall yaribak`.

## Option 3: Run from git clone

This is useful for development, or if you prefer to keep the repo and run it
from there directly.

```bash
# Clone repository.
mkdir -p /path/to/git
git clone https://github.com/hirak99/yaribak

# Invoke.
/path/to/git/yaribak.sh --help
```

# Usage

## Common Invocation and Arguments

```bash
yaribak \
  --source /path/to/source \
  --backup-path /path/to/backups

# Optional args (run with --help to view description) -
# --dryrun
# --verbose
# --only-if-changed
# --min_ttl=7days
# --min-to-keep=5
# --max-to-keep=10
# --minimum-wait=2days
# --exclude source_subdir1 --exclude source_subdir2 ...
```

Note: Care must be taken to use different backup directories for different source directories.

## Example Usage

Maintain backups of the home directory -

```bash
# Create the backup directory.
mkdir -p /path/to/homdir_backups

# Call this every time you want to backup, or put it in cron.
# Past backups will be kept.
yaribak \
  --source ~ \
  --backup-path /path/to/homedir_backups \
  --verbose \
  --exclude .cache
```

The following structure will be generated in the backup directory (for this
example, after 3 calls) -
```
$ tree /path/to/homedir_backups -L 1
/path/to/homedir_backups
├── ysnap_20220306_232441
├── ysnap_20220312_080749
└── ysnap_20220314_110741
```

Each directory will have a full copy of the source.

# Features

## Conserves space across backups

The primary reason to use this over a simple `cp -r` is that it saves space.

Any file that remains unchanged will be hard linked, effectively resulting in
very little space consumption for multiple invocation if the source remains
largely unchanged.

```bash
$ # Size of source directory.
$ du -sh ~
6.5G /home/user1

$ # Say following backups were created by multiple invocations -
$ tree /path/to/homedir_backups -L 1
├── ysnap_20220314_110741
├── ysnap_20220314_110815
└── ysnap_20220314_110903

$ # Assuming multiple backups were created with no change in source,
$ # total size of backup will not increase (by much).
$ du -h /path/to/homedir_backups
6.5G /path/to/homedir_backups
```

## Fault Tolerance

If a backup is stopped abruptly in the middle, yaribak will recover next time
you run it.

# Testing

## Unit Tests

From the package root, run -
```python
scripts/runtests.sh
```

## Packaging Test

```python
scripts/rebuild_install_locally.sh
```

Note: This will also install it locally. Use `pip uninstall yaribak` if you do
not need it.

# Alternatives

## Comparison with Timeshift
[Timeshift](https://github.com/teejee2008/timeshift) is an excellent utility to
do one thing: backing up system.

It however cannot be used to backup any other directory, or to back up in user-selected destination.

This is an alternative to allow more control, but without conveniences like a
GUI and out-of-the-box automated backups.

# FAQ

## How do I set up periodic backups?
You will need to add the backup command to cron. There are [many excellent
tutorials](https://www.google.com/search?q=setting+up+cron+job+linux+tutorial),
for example [this one](https://opensource.com/article/17/11/how-use-cron-linux).

## Does it create hard links to original files?
No, even if they are on the same filesystem, backups will never be hard linked
to source by design. Creating hard link to original files will result in the
backups being modified if the original file is modified - that's something we do
not want.

## Can I use the same destination for different sources?
Using the same destination for different sources will result in the algorithm
not evaluating unchanged files correctly across invocations. So it is strongly
discouraged to use the same directory for different sources. Instead, assign
different destination directories for different sources.

## How do I restore?
You will need to manually copy all files from any of the backups to the source directory.

This can be done either by `cp -ar` -
```bash
# Save the existing files.
mv /path/to/source /path/to/source_old

# Restore.
cp -ar /path/to/backups/ysnap_20220314_110903/payload /path/to/source
```

Or using `rsync` -
```bash
# Warning: Existing files will be irrevokably modified or deleted.
rsync -aAXHv --delete \
  /path/to/backups/ysnap_20220314_110903/payload \
  /path/to/source
```
