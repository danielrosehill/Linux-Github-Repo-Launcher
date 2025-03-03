# Repository Opener

A PyQt-based GUI application for Linux that helps you browse, search, and open your Git repositories in different IDEs.

## Features

- Browse repositories from multiple directories:
  - My Repos: `/home/daniel/Development/git-repositories/My-Repos`
  - My Forks: `/home/daniel/Development/git-repositories/My-Forks`
  - My Clones: `/home/daniel/Development/git-repositories/Cloned-Repos`
- Manage repository paths:
  - Add, edit, and remove custom repository paths
  - Settings are saved in `~/.config/repo-opener-0225/settings.json`
- Instant keyword searching with fuzzy matching for quick repository finding
- Open repositories in different IDEs:
  - VS Code
  - Windsurf

## Requirements

- Python 3.6+
- PyQt5 or PyQt6
- fuzzywuzzy (for fuzzy matching)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/repo-opener.git
   cd repo-opener
   ```

2. Install dependencies:
   ```
   pip install PyQt6 fuzzywuzzy
   ```
   
   Or for PyQt5:
   ```
   pip install PyQt5 fuzzywuzzy
   ```

3. Make the script executable:
   ```
   chmod +x repo_opener.py
   ```

## Usage

1. Run the application:
   ```
   ./repo_opener.py
   ```

2. Use the search bar to find repositories by name
3. Select a repository from the list
4. Click "Open in VS Code" or "Open in Windsurf" to open the selected repository in your preferred IDE
5. Manage repository paths:
   - Click "Add Path" to add a new repository path
   - Click "Edit Path" to modify an existing path
   - Click "Remove Path" to delete a path
   - Changes are automatically saved to the configuration file

## Customization

You can modify the default repository paths in the `repo_opener.py` file by changing the `DEFAULT_REPO_PATHS` dictionary.

## Building a Standalone Executable

The repository includes a build script to create a standalone executable using PyInstaller.

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```
   ./build.py
   ```

3. The executable will be created in the `dist` directory.

4. You can run the executable directly:
   ```
   ./dist/repo-opener
   ```