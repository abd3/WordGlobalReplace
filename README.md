# Global Word Document Find & Replace

A powerful web application for finding and replacing text across multiple Microsoft Word documents with an intuitive interface that shows context and allows selective replacements.

## Features

- **Global Search**: Search across multiple Word documents in a directory
- **Context Display**: View text with surrounding context for each match
- **Selective Replacement**: Choose which instances to replace individually
- **Bulk Operations**: Replace all selected instances at once
- **Interactive Interface**: Modern web UI with real-time feedback
- **Backup Creation**: Automatic backup of original files before modifications
- **File Validation**: Verify directories and Word files before processing

## Screenshots

The application provides a clean, modern interface with:
- Directory validation and file counting
- Search results with highlighted matches
- Editable replacement text for each occurrence
- Individual and bulk replacement options
- Real-time status updates

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone or download the application**:
   ```bash
   git clone <repository-url>
   cd WordGlobalReplace
   ```

2. **Install dependencies**:
   ```bash
   python3 -m pip install --user -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5130
   ```
   *(Use `WORD_GLOBAL_REPLACE_PORT` to change the port if needed.)*

## Usage

### Basic Workflow

1. **Enter Directory Path**: Specify the folder containing your Word documents
2. **Validate Directory**: Click "Validate" to check the directory and count Word files
3. **Enter Search Term**: Type the text you want to find
4. **Enter Replacement Text**: Type what you want to replace it with (optional)
5. **Set Context**: Adjust how much surrounding text to show (default: 150 characters)
6. **Search**: Click "Search Documents" to find all occurrences
7. **Review Results**: Examine each match with its context
8. **Edit Replacements**: Modify the replacement text for each occurrence if needed
9. **Replace**: Use individual "Replace" buttons or "Replace All Selected"

### Advanced Features

- **Selective Replacement**: Check/uncheck specific occurrences before bulk replacement
- **Context Adjustment**: Increase or decrease the amount of context shown around matches
- **File Information**: See which file each occurrence is in
- **Backup Safety**: Original files are automatically backed up before any changes

## File Structure

```
WordGlobalReplace/
├── app.py                          # Main Flask application
├── word_processor.py              # Basic Word document processing
├── advanced_word_processor.py      # Enhanced processing with context
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── templates/
│   └── index.html                 # Main web interface
├── static/
│   ├── style.css                  # CSS styling
│   └── script.js                  # JavaScript functionality
└── backups/                       # Automatic backups (created on first run)
```

## API Endpoints

The application provides several REST API endpoints:

- `POST /api/validate_directory` - Validate a directory path
- `POST /api/search` - Search for text in documents
- `POST /api/replace` - Replace text in a specific occurrence
- `POST /api/replace_all` - Replace multiple occurrences

## Command Line Usage

You can also use the processing scripts directly from the command line:

### Basic Search
```bash
python word_processor.py /path/to/documents "search term"
```

### Advanced Search
```bash
python advanced_word_processor.py /path/to/documents "search term"
```

## Supported File Types

- `.docx` (Microsoft Word 2007 and later)
- `.doc` (Microsoft Word 97-2003) - Limited support

## Safety Features

- **Automatic Backups**: Original files are backed up before any modifications
- **Confirmation Dialogs**: Bulk operations require user confirmation
- **Error Handling**: Comprehensive error reporting and recovery
- **Validation**: Directory and file validation before processing

## Troubleshooting

### Common Issues

1. **"python-docx library not found"**
   - Run: `pip install python-docx`

2. **"Directory does not exist"**
   - Check the directory path is correct
   - Ensure you have read permissions

3. **"No Word files found"**
   - Verify the directory contains `.docx` or `.doc` files
   - Check file extensions are correct

4. **"Permission denied"**
   - Ensure you have write permissions for the directory
   - Check if files are open in Microsoft Word

### Performance Tips

- For large directories, consider searching subdirectories separately
- Use specific search terms to reduce results
- Close Word documents before processing

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Adding New Features

The application is modular and can be extended:

- Add new file format support in `word_processor.py`
- Enhance the UI in `templates/index.html` and `static/style.css`
- Add new API endpoints in `app.py`

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the error messages in the application
3. Check the browser console for JavaScript errors
4. Verify all dependencies are installed correctly

