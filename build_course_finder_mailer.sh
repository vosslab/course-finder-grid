#!/bin/bash

# Build and locally sign the stable Mail.app Automation helper.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SOURCE_DIR="$REPO_ROOT/course_finder_mailer"
APP_PATH="$REPO_ROOT/CourseFinderMailer.app"
BUILD_DIR="$REPO_ROOT/build/course_finder_mailer"
MODULE_CACHE="$REPO_ROOT/build/swift_module_cache"
TEMP_APP="$BUILD_DIR/CourseFinderMailer.app"
BACKUP_APP="$BUILD_DIR/CourseFinderMailer.previous.app"
TEMP_EXECUTABLE="$TEMP_APP/Contents/MacOS/CourseFinderMailer"

# All build and install paths come from the trusted Git root (ASVS 5.3.2).
rm -rf "$TEMP_APP"
if [ -e "$BACKUP_APP" ]; then
	echo "ERROR: Preserving unexpected prior backup at $BACKUP_APP" >&2
	exit 1
fi
mkdir -p "$TEMP_APP/Contents/MacOS" "$MODULE_CACHE"
cp "$SOURCE_DIR/Info.plist" "$TEMP_APP/Contents/Info.plist"

xcrun swiftc \
	-module-cache-path "$MODULE_CACHE" \
	-O \
	-framework AppKit \
	-framework OSAKit \
	"$SOURCE_DIR/course_finder_mailer.swift" \
	-o "$TEMP_EXECUTABLE"

# Harden and identify the single Mail capability that the user approves in TCC
# (ASVS 8.1.1 and 13.1.1).
codesign --force --sign - --options runtime \
	--entitlements "$SOURCE_DIR/course_finder_mailer.entitlements" \
	"$TEMP_APP"
codesign --verify --deep --strict "$TEMP_APP"
plutil -lint "$TEMP_APP/Contents/Info.plist"

HAD_PREVIOUS_APP=0
if [ -e "$APP_PATH" ]; then
	mv "$APP_PATH" "$BACKUP_APP"
	HAD_PREVIOUS_APP=1
fi
if ! mv "$TEMP_APP" "$APP_PATH"; then
	if [ "$HAD_PREVIOUS_APP" -eq 1 ]; then
		if ! mv "$BACKUP_APP" "$APP_PATH"; then
			echo "ERROR: Previous app remains at $BACKUP_APP" >&2
			exit 1
		fi
		echo "ERROR: Could not install CourseFinderMailer.app; restored the previous app." >&2
	else
		echo "ERROR: Could not install CourseFinderMailer.app." >&2
	fi
	exit 1
fi
if [ "$HAD_PREVIOUS_APP" -eq 1 ]; then
	rm -rf "$BACKUP_APP"
fi

echo "Built $APP_PATH"
echo "Run source source_me.sh && python3 test_email_permission.py"
echo "and allow CourseFinderMailer to control Mail if macOS asks."
