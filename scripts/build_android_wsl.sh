#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/.buildozer-venv"
BUILDOZER_SOURCE="/mnt/c/Users/abdul/Desktop/kivy-buildozer-b4ae422"

if [[ ! -d "$BUILDOZER_SOURCE" ]]; then
  echo "Buildozer source folder was not found: $BUILDOZER_SOURCE" >&2
  exit 1
fi

cd "$PROJECT_ROOT"

sudo apt update
sudo apt install -y \
  autoconf automake build-essential ccache cmake gettext git \
  libffi-dev libltdl-dev libssl-dev libtool openjdk-17-jdk \
  patch pkg-config python3-pip python3-setuptools python3-venv \
  unzip zip zlib1g-dev

python3 -m venv "$BUILD_DIR"
source "$BUILD_DIR/bin/activate"
python -m pip install --upgrade pip wheel
python -m pip install "Cython<3.0" -e "$BUILDOZER_SOURCE"

buildozer -v android debug
