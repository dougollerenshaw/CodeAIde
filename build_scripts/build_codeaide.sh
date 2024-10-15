#!/bin/bash

# Exit on any error
set -e

# Activate the correct conda environment
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

# Install required packages
echo "Installing required Python packages..."
$PYTHON_PATH -m pip install --upgrade pip
$PYTHON_PATH -m pip install -r requirements.txt

# Check if Whisper is installed
echo "Checking Whisper installation..."
$PYTHON_PATH -c "import whisper; print('Whisper version:', whisper.__version__)"

# Package the application
echo "Packaging the application..."
yes | $PYTHON_PATH -m PyInstaller build_scripts/codeaide.spec

# Create the DMG
echo "Creating DMG..."
APP_NAME="CodeAide"
DMG_NAME="${APP_NAME}.dmg"
SOURCE_DIR="dist/${APP_NAME}.app"
FINAL_DMG="${DMG_NAME}"

# Create a temporary directory for DMG contents
TEMP_DIR=$(mktemp -d)
cp -R "${SOURCE_DIR}" "${TEMP_DIR}"
ln -s /Applications "${TEMP_DIR}"

# Create the DMG
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

echo "Build process completed successfully!"
echo "The DMG is ready for testing. (Not signed or notarized)"
