# Automated File Organizer

![Tests](https://github.com/yourusername/automated-file-organizer/actions/workflows/tests.yml/badge.svg)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python-based tool for automatically organizing files into categorized folders based on their file extensions. The organizer supports both built-in categorization rules and user-defined custom configurations.

## Features

- **Automatic File Categorization**: Organize files by extension into predefined categories
- **Custom Configuration**: Define your own categories and file type mappings
- **Built-in Categories**: Pre-configured categories for common file types
- **Dry-run Mode**: Preview what files would be moved before committing
- **Overwrite Protection**: Configurable handling of existing files
- **Comprehensive Logging**: Detailed operation tracking and error reporting
- **Recursive Scanning**: Organize files in subdirectories automatically
- **Cross-platform Support**: Works on Windows, macOS, and Linux (via Docker)

## Built-in Categories

The organizer comes with predefined categories for common file types:

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.wmv`, `.flv`, `.webm`
- **Music**: `.mp3`, `.wav`, `.flac`, `.aac`
- **Archives**: `.zip`, `.rar`, `.tar`, `.gz`, `.7z`
- **Code**: `.py`, `.java`, `.cpp`, `.js`, `.ts`, `.html`, `.css`
- **Others**: Any files that don't match the above categories

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/automated-file-organizer.git
cd automated-file-organizer
```

2. Install Docker
Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/) .
Verify installation:
```bash
docker --version
```

3. Build the Docker Image
```bash
docker build -t file-organizer:latest .
```
4. Copy the path
Copy the path of the folder which you want to clean up/organize.

## 5. Run the Organizer

Run with Docker, mounting your folder into the container:

### Example: (without using config file)
**Windows (PowerShell):** 
#### Remember to change the 'C:\Users\YourName\Downloads\testfiles' to your path
```bash
docker run --rm -v "C:\Users\YourName\Downloads\testfiles:/data" file-organizer:latest --source /data --verbose
```

**macOS/Linux:**
#### Remember to change the '/Downloads/testfiles' to your path
```bash
docker run --rm -v ~/Downloads/testfiles:/data file-organizer:latest --source /data --verbose
```
### Example: (using config file)
**Windows (PowerShell):**
#### Remember to change the 'C:\Users\YourName\Downloads\testfiles' and 'C:\Users\YourName' to your path
```bash
docker run --rm `
  -v "C:\Users\YourName\Downloads\testfiles:/data" `
  -v "C:\Users\YourName\.fileorganizer.json:/config/config.json" `
  file-organizer:latest --source /data --config /config/config.json --verbose
```

**macOS/Linux:**
#### Remember to change the '/Downloads/testfiles' to your path
```bash
docker run --rm \
  -v ~/Downloads/testfiles:/data \
  -v ~/.fileorganizer.json:/config/config.json \
  file-organizer:latest --source /data --config /config/config.json --verbose
```

## 6. Check Results

Your folder is now neatly organized:

```
folder/
├── Documents/
│   └── report.pdf
├── Images/
│   └── photo.png
├── Music/
│   └── song.mp3
├── Videos/
│   └── movie.mp4
├── Archives/
│   └── random.zip
└── Others/
    └── unknown.xyz
```


## Usage Examples

### Basic Usage

Organize files in your Downloads folder:

```python
from organizer.file_mover import FileMover
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Create organizer instance
organizer = FileMover('/path/to/your/downloads', {}, logger=logger)

# Preview what would happen (dry run)
organizer.organize(dry_run=True)

# Actually organize the files
organizer.organize()
```

### Command Line Usage

You can also run the organizer from the command line:

```bash
# Navigate to the organizer directory
cd organizer

# Run the organizer on a specific folder
python -c "
from file_mover import FileMover
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

organizer = FileMover('/path/to/organize', {}, logger=logger)
organizer.organize(dry_run=True)  # Remove dry_run=True to actually move files
"
```

### Advanced Usage

```python
from organizer.file_mover import FileMover
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('file_organizer')

# Create organizer
organizer = FileMover('/Users/john/Downloads', {}, logger=logger)

# Organize with overwrite enabled
organizer.organize(overwrite=True)

# Or organize specific files
organizer.move_file('/Users/john/Downloads/report.pdf', category='work_documents')
```

## Custom Configuration

You can customize the file categorization by creating a `.fileorganizer.json` configuration file.

### Configuration File Setup

1. Create a `.fileorganizer.json` file in your project directory or any parent directory
2. Define your custom categories and file extensions:

```json
{
  "WorkDocuments": [".docx", ".xlsx", ".pptx"],
  "PersonalPhotos": [".jpg", ".png", ".heic"],
  "ProjectFiles": [".psd", ".ai", ".sketch"],
  "CustomCategory": [".xyz", ".custom"],
  "Archives": [".zip", ".rar", ".tar.gz"]
}
```

### Configuration Rules

- **Priority**: Custom configurations override built-in categories
- **Case Sensitivity**: File extensions are matched case-insensitively
- **Category Names**: Will be converted to lowercase for folder names
- **File Search**: The organizer searches up the directory tree for `.fileorganizer.json`
- **Fallback**: If no config is found, built-in categories are used

### Configuration Examples

#### Developer Configuration
```json
{
  "Frontend": [".html", ".css", ".js", ".tsx", ".jsx"],
  "Backend": [".py", ".java", ".go", ".rs"],
  "Config": [".json", ".yaml", ".yml", ".toml"],
  "Database": [".sql", ".db", ".sqlite"],
  "Documentation": [".md", ".rst", ".txt"]
}
```

#### Designer Configuration
```json
{
  "GraphicDesign": [".psd", ".ai", ".eps", ".svg"],
  "Photography": [".raw", ".cr2", ".nef", ".dng"],
  "WebAssets": [".png", ".jpg", ".gif", ".webp"],
  "Fonts": [".ttf", ".otf", ".woff", ".woff2"]
}
```

#### Student Configuration
```json
{
  "Assignments": [".docx", ".pdf", ".txt"],
  "Presentations": [".pptx", ".key"],
  "Spreadsheets": [".xlsx", ".csv"],
  "Research": [".pdf", ".epub"],
  "Media": [".mp4", ".mp3", ".jpg", ".png"]
}
```

## Running Tests

The project includes comprehensive unit tests to ensure reliability and correctness.

### Test Setup

1. Ensure you're in the project root directory:
```bash
cd automated-file-organizer
```

2. Run all tests:
```bash
python -m pytest tests/ -v
```

### Running Specific Test Categories

```bash
# Run only file mover tests
python -m pytest tests/test_file_mover.py -v

# Run only configuration tests
python -m pytest tests/test_config.py -v

# Run tests with coverage report
python -m pytest tests/ --cov=organizer --cov-report=html
```

### Test Categories

The test suite covers:

- **File Movement Operations**: Testing file scanning, categorization, and movement
- **Configuration Loading**: Testing custom config file parsing and validation
- **User Config Integration**: Testing how custom configurations override built-in rules
- **Error Handling**: Testing graceful handling of various error conditions
- **Edge Cases**: Testing behavior with invalid files, permissions, etc.

### Example Test Output

```bash
$ python -m pytest tests/ -v

======================== test session starts ========================
collecting ... collected 25 items

tests/test_file_mover.py::test_categorize_file_builtin PASSED
tests/test_file_mover.py::test_categorize_file_config_override PASSED
tests/test_file_mover.py::test_categorize_file_case_insensitive PASSED
tests/test_file_mover.py::test_config_priority_over_builtin PASSED
tests/test_file_mover.py::test_fallback_to_builtin_when_no_config PASSED
tests/test_file_mover.py::test_unknown_extension_returns_others PASSED
...

======================== 25 passed in 2.34s ========================
```

📂 Project Structure
automated-file-organizer/
├── organizer/              # Core logic
│   └── file_mover.py
├── tests/                  # Test suite
├── Dockerfile              # Container setup
├── .dockerignore           # Files excluded from Docker build
├── requirements.txt        # Python dependencies
└── README.md               # Documentation

🧑‍💻 Author
Ruhe Tarannum 
Python Developer Intern @ Soft Nexis Technologies

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

**Files not being moved:**
- Check file permissions
- Ensure the source directory exists
- Verify logging output for error messages

## 🔧 Custom Configuration

By default, if no config file exists, the organizer will automatically generate a `.fileorganizer.json` file in your working directory on the first run.

Example auto-generated config:

```json
{
    "source_folder": "C:/Users/YourName/Downloads",
    "destination_folders": {
        "Documents": "C:/Users/YourName/Documents",
        "Images": "C:/Users/YourName/Pictures",
        "Videos": "C:/Users/YourName/Videos",
        "Music": "C:/Users/YourName/Music",
        "Archives": "C:/Users/YourName/Archives",
        "Code": "C:/Users/YourName/Code",
        "Others": "C:/Users/YourName/Others"
    }
}
```

**Permission errors:**
- Run with appropriate permissions
- Check that files aren't currently in use by other applications
- Ensure write permissions in the target directory

### Getting Help

- Check the logs for detailed error information
- Run in dry-run mode first to preview operations
- Ensure all file paths are accessible and valid
- Review the configuration file format and syntax
