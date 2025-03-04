#!/usr/bin/env python3
"""
Repo Opener - A GUI application to browse and open Git repositories
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from functools import partial

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                QListWidget, QListWidgetItem, QCheckBox, QGroupBox,
                                QDialog, QFormLayout, QMessageBox, QFileDialog, QStyle,
                                QTabWidget)
    from PyQt6.QtCore import Qt, QSize, QRect
    from PyQt6.QtGui import QIcon, QColor
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                QListWidget, QListWidgetItem, QCheckBox, QGroupBox,
                                QDialog, QFormLayout, QMessageBox, QFileDialog, QStyle,
                                QTabWidget)
    from PyQt5.QtCore import Qt, QSize, QRect
    from PyQt5.QtGui import QIcon, QColor
    PYQT_VERSION = 5

# Fuzzy matching library
try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("fuzzywuzzy library not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fuzzywuzzy"])
    from fuzzywuzzy import fuzz

# Default repository paths
DEFAULT_REPO_PATHS = {
    "My Repos": Path.home() / "Development" / "git-repositories" / "My-Repos",
    "My Forks": Path.home() / "Development" / "git-repositories" / "My-Forks",
    "My Clones": Path.home() / "Development" / "git-repositories" / "Cloned-Repos"
}
# Config directory
CONFIG_DIR = Path.home() / ".config" / "repo-opener-0225"

class RepoOpener(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repository Opener")
        self.setMinimumSize(850, 600)
        
        # Initialize config directory and load settings
        self.init_config()
        self.repo_paths = self.load_settings()
        
        # Store all repositories
        self.all_repos = {}
        
        # Setup UI
        self.init_ui()

        # Apply stylesheet
        self.apply_stylesheet()
        
        # Load repositories
        self.load_repositories()
    
    def init_config(self):
        """Initialize the configuration directory"""
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_settings(self):
        """Load settings from config file"""
        config_file = CONFIG_DIR / "settings.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                # Convert string paths to Path objects
                for name, path in settings.items():
                    settings[name] = Path(path)
                return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
                return dict(DEFAULT_REPO_PATHS)
        else:
            return dict(DEFAULT_REPO_PATHS)
    
    def save_settings(self):
        """Save settings to config file"""
        config_file = CONFIG_DIR / "settings.json"
        # Convert Path objects to strings for JSON serialization
        settings = {name: str(path) for name, path in self.repo_paths.items()}
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=4)
    
    def apply_stylesheet(self):
        """Apply stylesheet to make UI less overwhelming"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f9f9f9;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QListWidget {
                border: 1px solid #dcdcdc;
                background-color: white;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-bottom-color: #dcdcdc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 6px 12px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create Recent Repositories tab
        self.recent_tab = QWidget()
        recent_layout = QVBoxLayout(self.recent_tab)
        
        # Create Search Repositories tab
        self.search_tab = QWidget()
        search_layout = QVBoxLayout(self.search_tab)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.recent_tab, "Recent Repositories")
        self.tab_widget.addTab(self.search_tab, "Search Repositories")
        
        # Repository source checkboxes - shared between tabs
        sources_group = QGroupBox("Repository Sources") 
        sources_group.setObjectName("RepositorySources")
        sources_layout = QHBoxLayout()
        
        self.source_checkboxes = {}
        for source_name in self.repo_paths.keys():
            checkbox = QCheckBox(source_name)
            checkbox.setChecked(True)  # Default to checked
            checkbox.stateChanged.connect(self.load_repositories)
            sources_layout.addWidget(checkbox)
            self.source_checkboxes[source_name] = checkbox
        
        sources_group.setLayout(sources_layout)
        
        # Path management buttons - shared between tabs
        path_buttons_layout = QHBoxLayout()
        
        self.add_path_button = QPushButton("Add Path")
        self.add_path_button.clicked.connect(self.add_repository_path)
        self.edit_path_button = QPushButton("Edit Path")
        self.edit_path_button.clicked.connect(self.edit_repository_path)
        self.remove_path_button = QPushButton("Remove Path")
        self.remove_path_button.clicked.connect(self.remove_repository_path)
        
        path_buttons_layout.addWidget(self.add_path_button)
        path_buttons_layout.addWidget(self.edit_path_button)
        path_buttons_layout.addWidget(self.remove_path_button)
        
        # Add shared components to main layout
        main_layout.addWidget(sources_group)
        main_layout.addLayout(path_buttons_layout)
        
        # Setup Recent Repositories tab
        self.recent_repo_list = QListWidget()
        self.recent_repo_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.recent_repo_list.setSpacing(2)
        self.recent_repo_list.setAlternatingRowColors(True)
        recent_layout.addWidget(self.recent_repo_list)
        
        # Setup Search Repositories tab
        # Search bar
        search_bar_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #dcdcdc; border-radius: 4px;")
        self.search_input.setPlaceholderText("Type to search repositories...")
        self.search_input.textChanged.connect(self.filter_repositories)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.search_input)
        search_layout.addLayout(search_bar_layout)
        
        # Repository list for search tab
        self.search_repo_list = QListWidget()
        self.search_repo_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.search_repo_list.setSpacing(2)
        self.search_repo_list.setAlternatingRowColors(True)
        search_layout.addWidget(self.search_repo_list)
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Open buttons - shared between tabs
        buttons_layout = QHBoxLayout()
        
        self.vscode_button = QPushButton("Open in VS Code")
        self.vscode_button.clicked.connect(self.open_selected_repo)
        
        self.windsurf_button = QPushButton("Open in Windsurf")
        self.windsurf_button.clicked.connect(self.open_selected_repo_windsurf)
        
        buttons_layout.addWidget(self.vscode_button)
        buttons_layout.addWidget(self.windsurf_button)
        main_layout.addLayout(buttons_layout)
        
        # Set the main widget
        self.setCentralWidget(main_widget)

    def load_repositories(self):
        # Clear existing items
        self.recent_repo_list.clear()
        self.search_repo_list.clear()
        self.all_repos = {}
        
        # Get selected sources from checkboxes
        selected_sources = [name for name, checkbox in self.source_checkboxes.items() 
                           if checkbox.isChecked()]
        
        # Load repositories from selected paths
        for source_name in selected_sources:
            source_path = self.repo_paths[source_name]
            if source_path.exists():
                for item in source_path.iterdir():
                    if item.is_dir() and (item / ".git").exists():
                        # Get repository creation time
                        try:
                            # Try to get the creation time from the .git directory
                            git_dir = item / ".git"
                            creation_time = git_dir.stat().st_mtime
                        except Exception:
                            # Fallback to directory creation time
                            creation_time = item.stat().st_mtime
                        
                        self.all_repos[item.name] = {
                            "name": item.name,
                            "path": str(item),
                            "source": source_name,
                            "creation_time": creation_time
                        }
        
        # Add to search list widget (alphabetically sorted)
        for repo_name, repo_info in sorted(self.all_repos.items(), key=lambda x: x[0].lower()):
            item = CustomRepoListItem(repo_name, self.get_repo_type(repo_info['source']))
            item.setData(Qt.ItemDataRole.UserRole, repo_info)
            self.search_repo_list.addItem(item)
        
        # Add to recent list widget (sorted by creation time, newest first)
        for repo_name, repo_info in sorted(self.all_repos.items(), key=lambda x: x[1]['creation_time'], reverse=True):
            item = CustomRepoListItem(repo_name, self.get_repo_type(repo_info['source']))
            item.setData(Qt.ItemDataRole.UserRole, repo_info)
            self.recent_repo_list.addItem(item)

    def filter_repositories(self):
        search_text = self.search_input.text().lower()

        if not search_text:
            # If search is empty, show all repositories
            self.search_repo_list.clear()
            for repo_name, repo_info in sorted(self.all_repos.items(), key=lambda x: x[0].lower()):
                item = CustomRepoListItem(repo_name, self.get_repo_type(repo_info['source']))
                item.setData(Qt.ItemDataRole.UserRole, repo_info)
                self.search_repo_list.addItem(item)
            return

        # Clear the list
        self.search_repo_list.clear()

        # Filter repositories using fuzzy matching
        matches = []
        for repo_name, repo_info in self.all_repos.items():
            # Calculate fuzzy match score
            score = fuzz.partial_ratio(search_text, repo_name.lower())
            if score > 50:  # Threshold for matching
                matches.append((score, repo_name, repo_info))

        # Group matches by score
        score_groups = {}
        for score, repo_name, repo_info in matches:
            score_groups.setdefault(score, []).append((repo_name, repo_info))

        # Add matches to list, sorted by score (descending) and then alphabetically within each score group
        for score in sorted(score_groups.keys(), reverse=True):
            for repo_name, repo_info in sorted(score_groups[score], key=lambda x: x[0].lower()):
                item = CustomRepoListItem(repo_name, self.get_repo_type(repo_info['source']))
                item.setData(Qt.ItemDataRole.UserRole, repo_info)
                self.search_repo_list.addItem(item)

    def open_selected_repo(self):
        # Determine which tab is active and get the appropriate list widget
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index == 0:  # Recent Repositories tab
            selected_items = self.recent_repo_list.selectedItems()
        else:  # Search Repositories tab
            selected_items = self.search_repo_list.selectedItems()
        
        if not selected_items:
            return
        
        # Get repository info
        repo_info = selected_items[0].data(Qt.ItemDataRole.UserRole)
        repo_path = repo_info["path"]
        
        # Open the repository with VS Code
        try:
            subprocess.Popen(["code", repo_path])
        except Exception as e:
            print(f"Error opening repository: {e}")
    
    def open_selected_repo_windsurf(self):
        # Determine which tab is active and get the appropriate list widget
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index == 0:  # Recent Repositories tab
            selected_items = self.recent_repo_list.selectedItems()
        else:  # Search Repositories tab
            selected_items = self.search_repo_list.selectedItems()
        
        if not selected_items:
            return
        
        # Get repository info
        repo_info = selected_items[0].data(Qt.ItemDataRole.UserRole)
        repo_path = repo_info["path"]
        
        # Open the repository with Windsurf
        try:
            subprocess.Popen(["windsurf", repo_path])
        except Exception as e:
            print(f"Error opening repository: {e}")

    def add_repository_path(self):
        """Add a new repository path"""
        dialog = RepositoryPathDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_input.text()
            path = Path(dialog.path_input.text())
            
            # Validate inputs
            if not name or not path:
                QMessageBox.warning(self, "Invalid Input", "Name and path cannot be empty.")
                return
            
            if name in self.repo_paths:
                QMessageBox.warning(self, "Duplicate Name", f"A repository path with name '{name}' already exists.")
                return
            
            if not path.exists():
                QMessageBox.warning(self, "Invalid Path", f"The path '{path}' does not exist.")
                return
            
            # Add new path
            self.repo_paths[name] = path
            
            # Add checkbox for the new path
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.load_repositories)
            self.source_checkboxes[name] = checkbox
            
            # Add to layout
            sources_group = self.findChild(QGroupBox, "RepositorySources")
            if sources_group:
                sources_group.layout().addWidget(checkbox)
            
            # Save settings and reload repositories
            self.save_settings()
            self.load_repositories()
    
    def edit_repository_path(self):
        """Edit an existing repository path"""
        # Get list of path names
        path_names = list(self.repo_paths.keys())
        if not path_names:
            QMessageBox.information(self, "No Paths", "There are no repository paths to edit.")
            return
        
        # Create dialog to select which path to edit
        select_dialog = QDialog(self)
        select_dialog.setWindowTitle("Select Path to Edit")
        select_layout = QVBoxLayout(select_dialog)
        
        path_list = QListWidget()
        for name in path_names:
            path_list.addItem(name)
        select_layout.addWidget(path_list)
        
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(select_dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(select_dialog.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        select_layout.addLayout(buttons_layout)
        
        if select_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        selected_items = path_list.selectedItems()
        if not selected_items:
            return
        
        selected_name = selected_items[0].text()
        current_path = self.repo_paths[selected_name]
        
        # Open edit dialog
        dialog = RepositoryPathDialog(self)
        dialog.name_input.setText(selected_name)
        dialog.path_input.setText(str(current_path))
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.name_input.text()
            new_path = Path(dialog.path_input.text())
            
            # Validate inputs
            if not new_name or not new_path:
                QMessageBox.warning(self, "Invalid Input", "Name and path cannot be empty.")
                return
            
            if new_name != selected_name and new_name in self.repo_paths:
                QMessageBox.warning(self, "Duplicate Name", f"A repository path with name '{new_name}' already exists.")
                return
            
            if not new_path.exists():
                QMessageBox.warning(self, "Invalid Path", f"The path '{new_path}' does not exist.")
                return
            
            # Update path
            if new_name != selected_name:
                # Name changed, need to update checkbox
                del self.repo_paths[selected_name]
                self.repo_paths[new_name] = new_path
                
                # Update checkbox
                old_checkbox = self.source_checkboxes.pop(selected_name)
                sources_group = self.findChild(QGroupBox, "RepositorySources")
                if sources_group and old_checkbox:
                    sources_group.layout().removeWidget(old_checkbox)
                    old_checkbox.deleteLater()
                
                # Create new checkbox
                checkbox = QCheckBox(new_name)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self.load_repositories)
                self.source_checkboxes[new_name] = checkbox
                
                if sources_group:
                    sources_group.layout().addWidget(checkbox)
            else:
                # Just update the path
                self.repo_paths[selected_name] = new_path
            
            # Save settings and reload repositories
            self.save_settings()
            self.load_repositories()
    
    def remove_repository_path(self):
        """Remove an existing repository path"""
        # Get list of path names
        path_names = list(self.repo_paths.keys())
        if not path_names:
            QMessageBox.information(self, "No Paths", "There are no repository paths to remove.")
            return
        
        # Create dialog to select which path to remove
        select_dialog = QDialog(self)
        select_dialog.setWindowTitle("Select Path to Remove")
        select_layout = QVBoxLayout(select_dialog)
        
        path_list = QListWidget()
        for name in path_names:
            path_list.addItem(name)
        select_layout.addWidget(path_list)
        
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(select_dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(select_dialog.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        select_layout.addLayout(buttons_layout)
        
        if select_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        selected_items = path_list.selectedItems()
        if not selected_items:
            return
        
        selected_name = selected_items[0].text()
        
        # Confirm removal
        confirm = QMessageBox.question(
            self, 
            "Confirm Removal", 
            f"Are you sure you want to remove the repository path '{selected_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Remove path
            del self.repo_paths[selected_name]
            
            # Remove checkbox
            old_checkbox = self.source_checkboxes.pop(selected_name)
            sources_group = self.findChild(QGroupBox, "RepositorySources")
            if sources_group and old_checkbox:
                sources_group.layout().removeWidget(old_checkbox)
                old_checkbox.deleteLater()
            
            # Save settings and reload repositories
            self.save_settings()
            self.load_repositories()
    
    def get_repo_type(self, source_name):
        """Convert source name to repository type label"""
        if source_name == "My Repos":
            return "Repo"
        elif source_name == "My Forks":
            return "Fork"
        elif source_name == "My Clones":
            return "Clone"
        return source_name  # Default fallback


class CustomRepoListItem(QListWidgetItem):
    """Custom list item that displays repository name and source with better formatting"""
    def __init__(self, repo_name, source_name):
        super().__init__()
        self.repo_name = repo_name
        self.repo_type = source_name  # Now this is the repository type (Repo/Fork/Clone)
        self.setText(repo_name)  # Set basic text
        self.setSizeHint(QSize(0, 28))  # Slightly increase item height for better readability
    
    def paint(self, painter, option, widget):
        """Custom painting to offset the source name to the right"""
        # Call the parent class's paint method to handle selection highlighting
        super().paint(painter, option, widget)
        
        # Get the rectangle for the item
        rect = option.rect
        
        # Clear the default text
        painter.eraseRect(rect)
        
        # Draw selection background if item is selected
        # Handle different state flags between PyQt5 and PyQt6
        if PYQT_VERSION == 6:
            selected_state = QStyle.StateFlag.State_Selected
        else:
            selected_state = QStyle.StateFlag.State_Selected
        if option.state & selected_state:
            painter.fillRect(rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())
        
        # Draw repository name (left-aligned)
        font = painter.font()
        painter.drawText(rect.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.repo_name)
        
        # Draw repository type (right-aligned with padding)
        painter.setPen(Qt.GlobalColor.gray)
        # Use a colored background for the repository type
        type_rect = QRect(rect.right() - 70, rect.top() + 4, 60, rect.height() - 8)
        
        # Use different colors for different repository types
        if self.repo_type == "Repo":
            bg_color = QColor("#e6f7ff")  # Light blue
        elif self.repo_type == "Fork":
            bg_color = QColor("#f6ffed")  # Light green
        elif self.repo_type == "Clone":
            bg_color = QColor("#fff7e6")  # Light orange
        else:
            bg_color = QColor("#f0f0f0")  # Light gray (default)
            
        painter.fillRect(type_rect, bg_color)
        painter.setPen(QColor("#666666"))
        painter.drawRect(type_rect)  # Draw border
        painter.drawText(type_rect, Qt.AlignmentFlag.AlignCenter, self.repo_type)


class RepositoryPathDialog(QDialog):
    """Dialog for adding a new repository path"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repository Path")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Name input
        self.name_input = QLineEdit()
        layout.addRow("Name:", self.name_input)
        
        # Path input with browse button
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        layout.addRow("Path:", path_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow("", buttons_layout)
    
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_input.setText(directory)

def main():
    app = QApplication(sys.argv)
    window = RepoOpener()
    window.show()
    sys.exit(app.exec() if PYQT_VERSION == 6 else app.exec_())


if __name__ == "__main__":
    main()