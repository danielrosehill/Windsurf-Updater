# Windsurf-Updater

A GUI application to simplify the process of updating Windsurf IDE on non-Ubuntu Linux systems (tested on OpenSUSE Tumbleweed).

![Windsurf Updater Demo](updater.GIF)

## ⚠️ Disclaimer

**IMPORTANT: This is NOT an official Windsurf utility.**

- This tool is provided as-is, with no warranties or guarantees of any kind.
- Use at your own risk. No liability is accepted for any damage to your system resulting from the use of this tool.
- Always back up your important data before performing system updates.
- This is a temporary solution until Windsurf develops an official update mechanism.
- The developers of this tool are not affiliated with the official Windsurf team.

## Features

- Drag and drop interface for Windsurf tarball files
- Automatic detection of Windsurf installation location
- Backup of existing installation before updating
- Progress tracking during the update process
- Support for sudo operations when necessary

## Requirements

- Python 3.6 or higher
- PyQt6

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/danielrosehill/Windsurf-Updater.git
   cd Windsurf-Updater
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Building Distributable Packages

The repository includes a build script that can create standalone executables and AppImages for easy distribution:

1. Make the build script executable:
   ```
   chmod +x build.sh
   ```

2. Run the build script:
   ```
   ./build.sh
   ```

The script will:
- Check for required dependencies
- Build a standalone executable using PyInstaller
- Create an AppImage if the AppImageTool is installed
- Output the built files to the `dist` directory

### Build Requirements

- Python 3.6 or higher
- pip
- PyInstaller (will be installed automatically if missing)
- AppImageTool (optional, for AppImage creation)

## Usage

1. Run the application:
   ```
   python windsurf_updater.py
   ```

2. The application will attempt to automatically detect your Windsurf installation. If it cannot be found, you can manually specify the installation path.

3. Drag and drop the Windsurf tarball onto the application, or use the "Browse" button to select it.

4. Click "Update Windsurf" to begin the update process.

5. If the application doesn't have sufficient permissions to update the installation, it will prompt you to run with sudo privileges.

## How It Works

1. The application extracts the tarball to a temporary directory
2. Creates a backup of your current Windsurf installation
3. Copies the updated files to your installation directory
4. Cleans up temporary files

## Permissions Handling

The application handles permissions in several ways:

1. **Automatic Permission Detection**: The application automatically detects if it has sufficient permissions to update the Windsurf installation.

2. **Sudo Elevation**: If permissions are insufficient, it offers to run the update with sudo privileges using `pkexec`.

3. **Robust Extraction**: The application includes error handling during extraction to handle permission-related issues.

4. **Proper File Permissions**: When running with sudo, the application sets appropriate permissions on all installed files:
   - Directories: 755 (rwxr-xr-x)
   - Regular files: 644 (rw-r--r--)
   - Executable files: 755 (rwxr-xr-x)

5. **Feedback**: Detailed status messages are provided during the update process to help diagnose any issues.

## Troubleshooting

If you encounter permission issues:

1. Use the "Run with sudo" option when prompted
2. Ensure your user account has sudo privileges
3. Check that the target installation directory is accessible
4. For system directories like `/opt` or `/usr/local`, always use sudo

## License

This project is open source and available under the [MIT License](LICENSE).
