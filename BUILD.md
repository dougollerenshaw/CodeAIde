# CodeAide

CodeAide is a chat application that leverages LLMs to generate code based on users' natural language requests and allows users to run the code directly from the application.

## Building the Application

Follow these steps to build CodeAide as a standalone application for macOS:

Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Homebrew (for installing create-dmg)

### Step 1: Install Required Python Packages

```
pip install PyQt5 pyinstaller
```

### Step 2: Package the Application

1. Navigate to your project directory:
    ```
    cd path/to/CodeAIde
    ```

2. Run PyInstaller:
    ```
    pyinstaller --windowed --onefile --add-data "codeaide/examples.yaml:codeaide" codeaide.py
    ```
    This command creates a single executable file in the `dist` folder.

    Note: Make sure the path to examples.yaml is correct. If you're in the root of your project, it should be "codeaide/examples.yaml" as shown above.

### Step 3: Create an Application Bundle

1. Create the necessary directories:
    ```
    mkdir -p CodeAide.app/Contents/MacOS
    mkdir -p CodeAide.app/Contents/Resources
    ```

2. Move your executable:
    ```
    mv dist/codeaide CodeAide.app/Contents/MacOS/CodeAide
    ```

3. Create an `Info.plist` file in `CodeAide.app/Contents/`:
    ```
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>CFBundleExecutable</key>
        <string>CodeAide</string>
        <key>CFBundleIconFile</key>
        <string>icon.icns</string>
        <key>CFBundleIdentifier</key>
        <string>com.yourcompany.codeaide</string>
        <key>CFBundleName</key>
        <string>CodeAide</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>CFBundleShortVersionString</key>
        <string>1.0.0</string>
    </dict>
    </plist>
   ```

4. (Optional) Add an icon:
   - Create a .icns file for your app icon
   - Place it in `CodeAide.app/Contents/Resources/icon.icns`

### Step 4: Create the DMG

1. Install create-dmg:
    ```
    brew install create-dmg
    ```

2. Create the DMG:
    ```
    create-dmg \
        --volname "CodeAide Installer" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "CodeAide.app" 200 190 \
        --hide-extension "CodeAide.app" \
        --app-drop-link 600 185 \
        "CodeAide.dmg" \
        "CodeAide.app"
    ```

### Step 5: Test The Application

Always test the DMG on a clean macOS installation to ensure it works as expected.

Troubleshooting

If you encounter issues with resource files not being found:

1. Ensure all necessary files (like `examples.yaml`) are included in the PyInstaller command with the correct path.
2. Check the console output for any error messages.
3. Verify that the paths in `general_utils.py` are correct for both development and packaged environments.

Updating the Application

When updating the application:

1. Increment the version number in `Info.plist`.
2. Rebuild the application following the steps above.
3. Create a new DMG with the updated version.

Notes

- This README assumes you're building on macOS. The process may differ for other operating systems.