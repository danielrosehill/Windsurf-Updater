#!/bin/bash
# Build script for Windsurf Updater
# Generates both a standalone executable and an AppImage

# Version information
VERSION="1.0.0"

set -e  # Exit on error

echo "Windsurf Updater Build Script v$VERSION"
echo "============================="

# Check for required tools
check_dependencies() {
    echo "Checking dependencies..."
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is required but not installed."
        exit 1
    fi
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        echo "Error: pip3 is required but not installed."
        exit 1
    fi
    
    # Check for PyInstaller
    if ! pip3 list | grep -q pyinstaller; then
        echo "PyInstaller not found. Installing..."
        pip3 install pyinstaller
    fi
    
    # Check for AppImageTool (optional)
    if ! command -v appimagetool &> /dev/null; then
        echo "Warning: appimagetool not found. AppImage creation will be skipped."
        echo "To install appimagetool, visit: https://github.com/AppImage/AppImageKit/releases"
        BUILD_APPIMAGE=0
    else
        BUILD_APPIMAGE=1
    fi
}

# Install required Python packages
install_requirements() {
    echo "Installing Python requirements..."
    pip3 install -r requirements.txt
}

# Create a simple icon for the application
create_icon() {
    echo "Creating application icon..."
    mkdir -p "build/icons"
    ICON_PATH="build/icons/windsurf-updater.png"
    
    # Try to copy a system icon first
    if [ -f "/usr/share/icons/hicolor/256x256/apps/system-software-update.png" ]; then
        cp "/usr/share/icons/hicolor/256x256/apps/system-software-update.png" "$ICON_PATH"
        echo "Using system icon"
    elif [ -f "/usr/share/icons/hicolor/128x128/apps/system-software-update.png" ]; then
        cp "/usr/share/icons/hicolor/128x128/apps/system-software-update.png" "$ICON_PATH"
        echo "Using system icon"
    else
        # Create a minimal PNG file as fallback
        echo "No system icon found. Creating a minimal icon..."
        echo -e "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x15IDAT8\x8dcddbf\x00\x05\x8c\xa3\x01\x83\"\x00\x00\xde\x00\x0b\x00\x01\xa2\xdc\xef\xe6\x00\x00\x00\x00IEND\xaeB\x60\x82" > "$ICON_PATH"
    fi
}

# Build standalone executable with PyInstaller
build_executable() {
    echo "Building standalone executable with PyInstaller..."
    
    # Clean previous build artifacts
    rm -rf build/windsurf-updater dist
    rm -f windsurf-updater*.spec
    mkdir -p build
    
    # Create icon
    create_icon
    
    # Build with PyInstaller
    echo "Running PyInstaller..."
    pyinstaller --clean --onefile \
        --name "windsurf-updater-$VERSION" \
        --add-data "windsurf-updater.desktop:." \
        --windowed \
        windsurf_updater.py
    
    if [ $? -eq 0 ]; then
        echo "Standalone executable created at: dist/windsurf-updater-$VERSION"
    else
        echo "PyInstaller failed. Check the output above for errors."
        exit 1
    fi
}

# Build AppImage (if appimagetool is available)
build_appimage() {
    if [ "$BUILD_APPIMAGE" -eq 0 ]; then
        return
    fi
    
    echo "Building AppImage..."
    
    # Create AppDir structure
    APPDIR="dist/WindsurfUpdater.AppDir"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    
    # Check if executable exists
    if [ ! -f "dist/windsurf-updater-$VERSION" ]; then
        echo "Error: Executable not found. PyInstaller build may have failed."
        return 1
    fi
    
    # Copy executable
    cp "dist/windsurf-updater-$VERSION" "$APPDIR/usr/bin/windsurf-updater"
    
    # Copy desktop file
    cp windsurf-updater.desktop "$APPDIR/usr/share/applications/"
    cp windsurf-updater.desktop "$APPDIR/"
    
    # Create AppRun script
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
exec "${HERE}/usr/bin/windsurf-updater" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    
    # Copy icon to AppDir
    if [ -f "build/icons/windsurf-updater.png" ]; then
        cp "build/icons/windsurf-updater.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/system-software-update.png"
        ln -sf usr/share/icons/hicolor/256x256/apps/system-software-update.png "$APPDIR/system-software-update.png"
    else
        echo "Warning: Icon not found. AppImage will have no icon."
        touch "$APPDIR/system-software-update.png"
    fi
    
    # Build the AppImage
    echo "Creating AppImage..."
    cd dist
    ARCH=$(uname -m)
    
    if appimagetool WindsurfUpdater.AppDir "WindsurfUpdater-${VERSION}-${ARCH}.AppImage" 2>/dev/null; then
        echo "AppImage created at: dist/WindsurfUpdater-${VERSION}-${ARCH}.AppImage"
    else
        echo "Failed to create AppImage. Check if appimagetool is properly installed."
        cd ..
        return 1
    fi
    
    cd ..
    return 0
}

# Main build process
main() {
    check_dependencies
    install_requirements
    
    # Build executable
    if build_executable; then
        echo "Executable build successful."
    else
        echo "Executable build failed."
        exit 1
    fi
    
    # Build AppImage if possible
    if [ "$BUILD_APPIMAGE" -eq 1 ]; then
        if build_appimage; then
            echo "AppImage build successful."
        else
            echo "AppImage build failed, but executable was created successfully."
        fi
    fi
    
    echo ""
    echo "Build completed!"
    echo "Output files:"
    echo "  - Standalone executable: dist/windsurf-updater-$VERSION"
    if [ "$BUILD_APPIMAGE" -eq 1 ]; then
        ARCH=$(uname -m)
        if [ -f "dist/WindsurfUpdater-${VERSION}-${ARCH}.AppImage" ]; then
            echo "  - AppImage: dist/WindsurfUpdater-${VERSION}-${ARCH}.AppImage"
        fi
    fi
}

# Run the main function
main
