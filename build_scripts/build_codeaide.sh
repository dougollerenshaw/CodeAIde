#!/bin/bash

# Exit on any error
set -e

# Function to check if a command exists
command_exists () {
    type "$1" &> /dev/null ;
}

# Check prerequisites
if ! command_exists conda ; then
    echo "conda is not installed. Please install it and try again."
    exit 1
fi

if ! command_exists brew ; then
    echo "Homebrew is not installed. Please install it and try again."
    exit 1
fi

# Check if notarization is requested
NOTARIZE=false
if [ "$1" = "--notarize" ]; then
    NOTARIZE=true
fi

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate codeaide

# Get the path to the Python interpreter in the conda environment
PYTHON_PATH=$(which python)

# Change directory to the project root
cd "$(dirname "$0")/.."

# Ensure log directory exists
echo "Ensuring log directory exists..."
mkdir -p ~/Library/Logs/CodeAide

# Ensure application data directory exists
echo "Ensuring application data directory exists..."
mkdir -p ~/Library/Application\ Support/CodeAide

# Step 1: Install Required Python Packages and Download Whisper Model
echo "Installing required Python packages..."
$PYTHON_PATH -m pip install --upgrade pip
$PYTHON_PATH -m pip install PyQt5 pyinstaller whisper

echo "Downloading Whisper model..."
$PYTHON_PATH <<EOF
import whisper
whisper.load_model('tiny', download_root='./codeaide/models/whisper')
EOF

# Step 2: Package the Application
echo "Packaging the application..."
$PYTHON_PATH -m PyInstaller build_scripts/codeaide.spec

# Step 3: Create the DMG
echo "Creating DMG..."
APP_NAME="CodeAide"
DMG_NAME="${APP_NAME}.dmg"
SOURCE_DIR="dist/${APP_NAME}.app"
TEMP_DMG="temp_${DMG_NAME}"
FINAL_DMG="${DMG_NAME}"

# Clean up function
cleanup() {
    echo "Cleaning up..."
    for disk in $(diskutil list | grep ${APP_NAME} | awk '{print $NF}'); do
        echo "Attempting to unmount and eject $disk"
        diskutil unmountDisk force $disk 2>/dev/null || true
        diskutil eject force $disk 2>/dev/null || true
    done
    rm -f "${TEMP_DMG}"
}

# Run cleanup before starting
cleanup

# Create a temporary directory for DMG contents
TEMP_DIR=$(mktemp -d)
cp -R "${SOURCE_DIR}" "${TEMP_DIR}"
ln -s /Applications "${TEMP_DIR}"

# Create the DMG directly
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${TEMP_DIR}" -ov -format UDZO "${FINAL_DMG}"

# Clean up the temporary directory
rm -rf "${TEMP_DIR}"

# Verify that the DMG was created
if [ -f "${FINAL_DMG}" ]; then
    echo "DMG created successfully: ${FINAL_DMG}"
else
    echo "Error: DMG creation failed"
    exit 1
fi

if [ "$NOTARIZE" = true ]; then
    # Prompt for Apple Developer information
    read -p "Enter your Developer ID Application certificate name (e.g., 'Developer ID Application: Your Name'): " DEVELOPER_NAME
    read -p "Enter your Apple Developer Team ID: " TEAM_ID
    read -p "Enter your Apple ID: " APPLE_ID
    read -s -p "Enter your app-specific password: " APP_PASSWORD
    echo

    # Step 4: Code Sign the Application
    echo "Code signing the application..."
    codesign --force --options runtime --entitlements build_scripts/entitlements.plist --sign "$DEVELOPER_NAME" "dist/CodeAide.app"

    # Step 5: Notarize the DMG
    echo "Notarizing the DMG..."
    xcrun notarytool submit "${FINAL_DMG}" --wait --apple-id "$APPLE_ID" --password "$APP_PASSWORD" --team-id "$TEAM_ID"

    # Step 6: Staple the notarization ticket to the DMG
    echo "Stapling the notarization ticket..."
    xcrun stapler staple "${FINAL_DMG}"

    echo "Build process completed successfully!"
    echo "The signed and notarized DMG is ready for distribution."
else
    echo "Build process completed successfully!"
    echo "The DMG is ready for testing. (Not signed or notarized)"
fi

# Final cleanup
cleanup
