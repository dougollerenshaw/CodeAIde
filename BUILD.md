# CodeAide

CodeAide is a chat application that leverages LLMs to generate code based on users' natural language requests and allows users to run the code directly from the application.

## Building the Application

Follow these steps to build CodeAide as a standalone application for macOS:

### Prerequisites

- Python 3.11 or higher
- Conda (for managing the Python environment)
- Homebrew (for installing create-dmg)

### Step 1: Set Up the Environment

1. Create and activate a new conda environment:
   ```
   conda create -n codeaide python=3.11
   conda activate codeaide
   ```

2. Ensure you're in the project root directory.

### Step 2: Run the Build Script

1. Make the build script executable:
   ```
   chmod +x build_codeaide.sh
   ```

2. Run the build script:

   For local testing (without notarization):
   ```
   ./build_codeaide.sh
   ```

   For building a distributable version (with notarization):
   ```
   ./build_codeaide.sh --notarize
   ```

   If you choose to notarize, you will be prompted to enter:
   - Your Developer ID Application certificate name
   - Your Apple Developer Team ID
   - Your Apple ID
   - Your app-specific password

   Make sure you have these details ready before running the script with the --notarize option.

### Step 3: Test The Application

Always test the DMG on a clean macOS installation to ensure it works as expected.

## Troubleshooting

If you encounter issues:

1. Check the console output for any error messages.
2. Ensure all necessary files are included in the `codeaide.spec` file.
3. Verify that the paths in your code are correct for both development and packaged environments.
4. If you're having issues with PyInstaller, try updating it to the latest version:
   ```
   pip install --upgrade pyinstaller
   ```

## Updating the Application

When updating the application:

1. Update the version number in the `build_codeaide.sh` script (look for `CFBundleShortVersionString`).
2. Rebuild the application by running the build script.

## Notes

- This build process is designed for macOS. The process may differ for other operating systems.
- Ensure you're in the correct conda environment (`codeaide`) when running these commands.
- The `codeaide.spec` file is crucial for correct packaging. If you make changes to your project structure or dependencies, update the spec file accordingly.
