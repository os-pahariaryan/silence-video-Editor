#!/bin/sh
# Enable project git hooks (strips Cursor co-author from commits).
set -e
cd "$(dirname "$0")/.."
chmod +x .githooks/prepare-commit-msg
git config core.hooksPath .githooks
echo "Git hooks enabled: core.hooksPath=.githooks"
