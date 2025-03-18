#!/usr/bin/env python3
"""
Windsurf Updater - A GUI tool to update Windsurf IDE on Linux systems.
"""

import os
import sys
import tarfile
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFileDialog, QMessageBox, QProgressBar, QLineEdit
)
from PyQt6.QtCore import Qt, QMimeData, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont

# Version information
VERSION = "1.0.0"

class UpdaterThread(QThread):
    """Thread for handling the update process without blocking the UI."""
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, tarball_path, install_path):
        super().__init__()
        self.tarball_path = tarball_path
        self.install_path = install_path
        self.start_time = time.time()

    def run(self):
        try:
            self.status_signal.emit("Starting update process...")
            self.progress_signal.emit(10)

            # Create temporary directory for extraction in user's home directory
            temp_dir = Path(tempfile.mkdtemp(prefix="windsurf_update_"))
            self.status_signal.emit(f"Created temporary directory at {temp_dir}")
            
            # Ensure the temporary directory has proper permissions
            try:
                os.chmod(temp_dir, 0o755)
            except Exception as e:
                self.status_signal.emit(f"Warning: Could not set permissions on temp directory: {str(e)}")
            
            self.status_signal.emit("Extracting tarball...")
            self.progress_signal.emit(30)
            
            # Extract tarball to temporary directory with better error handling
            try:
                with tarfile.open(self.tarball_path, "r:gz") as tar:
                    # Check for problematic paths before extraction
                    for member in tar.getmembers():
                        if member.name.startswith('/') or '..' in member.name:
                            raise Exception(f"Potentially unsafe path in tarball: {member.name}")
                    
                    # Extract all files with proper error handling
                    for member in tar.getmembers():
                        try:
                            tar.extract(member, path=temp_dir)
                        except PermissionError:
                            self.status_signal.emit(f"Permission error extracting {member.name}, trying to continue...")
                            # Try to continue with other files
                            continue
                        except Exception as e:
                            self.status_signal.emit(f"Error extracting {member.name}: {str(e)}")
                            # Try to continue with other files
                            continue
            except Exception as e:
                raise Exception(f"Failed to extract tarball: {str(e)}")
            
            self.status_signal.emit("Backing up current installation...")
            self.progress_signal.emit(50)
            
            # Check if install path exists before trying to backup
            if Path(self.install_path).exists():
                # Backup current installation to user's home directory
                backup_dir = Path.home() / f"windsurf_backup_{int(self.start_time)}"
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.copytree(self.install_path, backup_dir)
                self.status_signal.emit(f"Backup created at {backup_dir}")
            else:
                # Create the installation directory if it doesn't exist
                try:
                    Path(self.install_path).mkdir(parents=True, exist_ok=True)
                    self.status_signal.emit("Created new installation directory")
                except PermissionError:
                    raise Exception("Permission denied when creating installation directory. Try running with sudo.")
            
            self.status_signal.emit("Updating Windsurf...")
            self.progress_signal.emit(70)
            
            # Find the extracted directory (it might be nested)
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                extracted_files = list(temp_dir.iterdir())
                if not extracted_files:
                    raise Exception("No files found in the extracted tarball")
                # If no directories but files exist, use temp_dir as source
                source_dir = temp_dir
            else:
                # Use the first directory as source
                source_dir = extracted_dirs[0]
            
            # Update the installation
            for item in source_dir.iterdir():
                dest_path = Path(self.install_path) / item.name
                try:
                    if dest_path.exists():
                        if dest_path.is_dir():
                            shutil.rmtree(dest_path)
                        else:
                            dest_path.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, dest_path)
                    else:
                        shutil.copy2(item, dest_path)
                except PermissionError:
                    raise Exception(f"Permission denied when copying {item.name}. Try running with sudo.")
                except Exception as e:
                    raise Exception(f"Error copying {item.name}: {str(e)}")
            
            self.status_signal.emit("Cleaning up...")
            self.progress_signal.emit(90)
            
            # Clean up with error handling
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.status_signal.emit(f"Warning: Could not clean up temporary directory: {str(e)}")
            
            self.progress_signal.emit(100)
            self.status_signal.emit("Update completed successfully!")
            self.finished_signal.emit(True, "Windsurf has been successfully updated!")
            
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, f"Update failed: {str(e)}")


class WindsurfUpdaterWindow(QMainWindow):
    """Main window for the Windsurf Updater application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Windsurf Updater v{VERSION}")
        self.setMinimumSize(600, 400)
        
        self.tarball_path = None
        self.windsurf_path = self.find_windsurf_installation()
        
        self.init_ui()
        
        # Show disclaimer dialog on startup
        self.show_disclaimer()
    
    def show_disclaimer(self):
        """Show a disclaimer dialog on startup."""
        disclaimer_text = (
            "<h3>⚠️ DISCLAIMER</h3>"
            "<p><b>This is NOT an official Windsurf utility.</b></p>"
            "<p>This tool is provided as-is, with no warranties or guarantees of any kind.</p>"
            "<p>Use at your own risk. No liability is accepted for any damage to your system "
            "resulting from the use of this tool.</p>"
            "<p>Always back up your important data before performing system updates.</p>"
            "<p>This is a temporary solution until Windsurf develops an official update mechanism.</p>"
        )
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Disclaimer")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(disclaimer_text)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Title
        title_label = QLabel(f"Windsurf Updater v{VERSION}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Disclaimer
        disclaimer_label = QLabel(
            "⚠️ DISCLAIMER: This is NOT an official Windsurf utility. Use at your own risk. ⚠️"
        )
        disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer_font = QFont()
        disclaimer_font.setItalic(True)
        disclaimer_label.setFont(disclaimer_font)
        disclaimer_label.setStyleSheet("color: #FF5733;")
        main_layout.addWidget(disclaimer_label)
        
        # Description
        desc_label = QLabel(
            "Drag and drop the Windsurf tarball below to update your installation."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc_label)
        
        # Drop area
        self.drop_area = QLabel("Drop Windsurf tarball here")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setStyleSheet(
            "border: 2px dashed #aaa; border-radius: 5px; padding: 10px;"
        )
        self.drop_area.setAcceptDrops(True)
        self.drop_area.dragEnterEvent = self.dragEnterEvent
        self.drop_area.dropEvent = self.dropEvent
        main_layout.addWidget(self.drop_area)
        
        # Browse button
        browse_button = QPushButton("Browse for tarball")
        browse_button.clicked.connect(self.browse_tarball)
        main_layout.addWidget(browse_button)
        
        # Windsurf installation path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Windsurf Installation Path:"))
        
        self.path_edit = QLineEdit(self.windsurf_path if self.windsurf_path else "")
        self.path_edit.setPlaceholderText("Path to Windsurf installation")
        path_layout.addWidget(self.path_edit)
        
        path_browse_button = QPushButton("Browse")
        path_browse_button.clicked.connect(self.browse_install_path)
        path_layout.addWidget(path_browse_button)
        
        main_layout.addLayout(path_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Update button
        self.update_button = QPushButton("Update Windsurf")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.setEnabled(False)
        main_layout.addWidget(self.update_button)
        
        self.setCentralWidget(main_widget)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for the drop area."""
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().endswith((".tar.gz", ".tgz")):
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for the drop area."""
        urls = event.mimeData().urls()
        if urls and len(urls) == 1:
            self.tarball_path = urls[0].toLocalFile()
            self.drop_area.setText(f"Selected: {os.path.basename(self.tarball_path)}")
            self.update_button.setEnabled(bool(self.windsurf_path))
            self.status_label.setText("Ready to update. Click 'Update Windsurf' to proceed.")
    
    def browse_tarball(self):
        """Open file dialog to select a tarball."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Windsurf Tarball", "", "Tarball Files (*.tar.gz *.tgz)"
        )
        if file_path:
            self.tarball_path = file_path
            self.drop_area.setText(f"Selected: {os.path.basename(self.tarball_path)}")
            self.update_button.setEnabled(bool(self.windsurf_path))
            self.status_label.setText("Ready to update. Click 'Update Windsurf' to proceed.")
    
    def browse_install_path(self):
        """Open directory dialog to select Windsurf installation path."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Windsurf Installation Directory", ""
        )
        if dir_path:
            self.windsurf_path = dir_path
            self.path_edit.setText(dir_path)
            self.update_button.setEnabled(bool(self.tarball_path))
    
    def find_windsurf_installation(self):
        """
        Attempt to find the Windsurf installation on the system.
        Returns the path if found, None otherwise.
        """
        # Common installation locations to check
        possible_locations = [
            Path.home() / "windsurf",
            Path.home() / "Windsurf",
            Path.home() / "Applications" / "windsurf",
            Path.home() / "Applications" / "Windsurf",
            Path("/opt/windsurf"),
            Path("/opt/Windsurf"),
            Path("/usr/local/windsurf"),
            Path("/usr/local/Windsurf"),
        ]
        
        # Check if any of these locations exist and contain windsurf executable
        for location in possible_locations:
            if location.exists() and (location / "windsurf").exists():
                return str(location)
            
            # Also check for windsurf executable with .sh extension
            if location.exists() and (location / "windsurf.sh").exists():
                return str(location)
        
        # Try to find using 'which' command
        try:
            result = subprocess.run(
                ["which", "windsurf"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                return str(Path(path).parent)
        except Exception:
            pass
        
        return None
    
    def start_update(self):
        """Start the update process."""
        if not self.tarball_path:
            QMessageBox.warning(self, "Error", "Please select a Windsurf tarball first.")
            return
        
        # Get the installation path from the text field (in case user modified it)
        self.windsurf_path = self.path_edit.text().strip()
        
        if not self.windsurf_path:
            QMessageBox.warning(self, "Error", "Please specify the Windsurf installation path.")
            return
        
        # Check if the installation path exists
        if not os.path.isdir(self.windsurf_path):
            result = QMessageBox.question(
                self,
                "Directory Not Found",
                f"The directory '{self.windsurf_path}' does not exist. Do you want to create it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(self.windsurf_path, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create directory: {str(e)}")
                    return
            else:
                return
        
        # Check if we have write permissions to the installation path
        if not os.access(self.windsurf_path, os.W_OK):
            result = QMessageBox.question(
                self,
                "Insufficient Permissions",
                "You don't have write permissions to the Windsurf installation directory. "
                "Do you want to run the update with sudo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                # Run the update with sudo
                self.run_with_sudo()
            return
        
        # Start the update thread
        self.progress_bar.setVisible(True)
        self.update_button.setEnabled(False)
        self.status_label.setText("Updating Windsurf...")
        
        self.update_thread = UpdaterThread(self.tarball_path, self.windsurf_path)
        self.update_thread.progress_signal.connect(self.update_progress)
        self.update_thread.status_signal.connect(self.update_status)
        self.update_thread.finished_signal.connect(self.update_finished)
        self.update_thread.start()
    
    def run_with_sudo(self):
        """Run the updater with sudo privileges."""
        try:
            # Create a temporary script that will run the update with sudo
            script_path = Path.home() / "windsurf_update_script.sh"
            with open(script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("set -e\n")  # Exit on error
                f.write("echo 'Starting Windsurf update with elevated privileges...'\n")
                
                # Create installation directory with proper permissions
                f.write(f"mkdir -p '{self.windsurf_path}'\n")
                f.write(f"chmod 755 '{self.windsurf_path}'\n")
                
                # Create a temporary directory in /tmp with proper permissions
                f.write("TEMP_DIR=$(mktemp -d -t windsurf_update_XXXXXX)\n")
                f.write("chmod 755 $TEMP_DIR\n")
                f.write("echo \"Created temporary directory at $TEMP_DIR\"\n")
                
                # Extract with proper error handling
                f.write("echo 'Extracting tarball...'\n")
                f.write(f"if ! tar -xzf '{self.tarball_path}' -C $TEMP_DIR; then\n")
                f.write("  echo 'Failed to extract tarball'\n")
                f.write("  rm -rf $TEMP_DIR\n")
                f.write("  exit 1\n")
                f.write("fi\n")
                
                # Create a backup if the installation exists
                f.write("echo 'Backing up current installation...'\n")
                f.write(f"if [ -d '{self.windsurf_path}' ] && [ -n \"$(ls -A '{self.windsurf_path}')\" ]; then\n")
                f.write(f"  BACKUP_DIR='{Path.home()}/windsurf_backup_$(date +%Y%m%d_%H%M%S)'\n")
                f.write(f"  mkdir -p \"$BACKUP_DIR\"\n")
                f.write(f"  chmod 755 \"$BACKUP_DIR\"\n")
                f.write(f"  cp -r '{self.windsurf_path}/'* \"$BACKUP_DIR/\" 2>/dev/null || true\n")
                f.write("  echo \"Backup created at $BACKUP_DIR\"\n")
                f.write("fi\n")
                
                # Copy the extracted files to the installation directory
                f.write("echo 'Updating Windsurf...'\n")
                f.write("EXTRACTED_DIR=$(find $TEMP_DIR -maxdepth 1 -type d | grep -v \"^$TEMP_DIR$\" | head -n 1)\n")
                f.write("if [ -z \"$EXTRACTED_DIR\" ]; then\n")
                f.write("  # No subdirectory found, use temp_dir as source\n")
                f.write("  EXTRACTED_DIR=$TEMP_DIR\n")
                f.write("fi\n")
                
                # Clear the destination directory first to avoid permission issues with existing files
                f.write(f"find '{self.windsurf_path}' -mindepth 1 -delete 2>/dev/null || true\n")
                
                # Copy with rsync if available, otherwise use cp
                f.write("if command -v rsync >/dev/null 2>&1; then\n")
                f.write(f"  rsync -a \"$EXTRACTED_DIR/\"* '{self.windsurf_path}/' 2>/dev/null || cp -r \"$EXTRACTED_DIR/\"* '{self.windsurf_path}/'\n")
                f.write("else\n")
                f.write(f"  cp -r \"$EXTRACTED_DIR/\"* '{self.windsurf_path}/'\n")
                f.write("fi\n")
                
                # Set proper permissions on the installed files
                f.write(f"find '{self.windsurf_path}' -type d -exec chmod 755 {{}} \\;\n")
                f.write(f"find '{self.windsurf_path}' -type f -exec chmod 644 {{}} \\;\n")
                f.write(f"find '{self.windsurf_path}' -type f -name \"*.sh\" -exec chmod 755 {{}} \\;\n")
                f.write(f"[ -f '{self.windsurf_path}/windsurf' ] && chmod 755 '{self.windsurf_path}/windsurf'\n")
                
                # Clean up
                f.write("echo 'Cleaning up...'\n")
                f.write("rm -rf $TEMP_DIR\n")
                f.write("echo \"Update completed successfully!\"\n")
            
            os.chmod(script_path, 0o755)
            
            # Run the script with sudo
            cmd = ["pkexec", "bash", str(script_path)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            QMessageBox.information(
                self,
                "Sudo Update",
                "A sudo prompt will appear. Please enter your password to continue with the update.\n\n"
                "The update will run in the background. You'll be notified when it's complete."
            )
            
            # Start a thread to monitor the process
            def monitor_process():
                stdout, stderr = process.communicate()
                success = process.returncode == 0
                
                if success:
                    message = "Windsurf has been successfully updated with sudo privileges!"
                    QApplication.instance().beep()
                    QMessageBox.information(self, "Update Complete", message)
                else:
                    error_message = f"Update failed with sudo:\n\n{stderr}"
                    QMessageBox.critical(self, "Update Failed", error_message)
                
                # Clean up the script
                try:
                    os.remove(script_path)
                except Exception:
                    pass
            
            monitor_thread = QThread()
            monitor_thread.run = monitor_process
            monitor_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run with sudo: {str(e)}")
    
    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update the status label."""
        self.status_label.setText(message)
    
    def update_finished(self, success, message):
        """Handle update completion."""
        self.progress_bar.setVisible(False)
        self.update_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Update Complete", message)
        else:
            QMessageBox.critical(self, "Update Failed", message)


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    window = WindsurfUpdaterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
