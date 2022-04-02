#!/bin/bash
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

# Script to build and install with pip locally.
set -uexo pipefail

readonly MY_PATH=$(cd $(dirname "$0") && pwd)

pushd $MY_PATH/..
trap "popd" EXIT

rm -f dist/*
python3 -m build

pip install dist/$(ls dist | grep whl) --force-reinstall

if ! ./yaribak.sh --help | grep -q "usage: yaribak .* \-\-source SOURCE"; then
  echo ERROR: Expected output not found on running yaribak --help.
  exit -1
fi

echo SUCCESS: Built and installed OK 👍
