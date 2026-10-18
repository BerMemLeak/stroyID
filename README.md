# StroyID Desktop

Desktop application for managing construction project documentation.

## Quick Start

### Prerequisites
- Python 3.8 or later
- Windows OS (for building executable)

### Setup and Build

Clone the repository and run the automated setup script:

```powershell
git clone <your-repo-url>
cd StroyID_Desktop_0.9.4
.\setup_and_build.ps1
```

This script will:
1. Check Python installation
2. Create a virtual environment
3. Install all dependencies
4. Build the executable

The built application will be available at `release\StroyID.exe`

### Manual Setup

If you prefer to set up manually:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-build.txt

# Run from source
.\run_windows.bat

# Or build executable
.\build_windows.ps1
```

## Development

### Running from Source
```powershell
.\run_windows.bat
```

### Building Executable
```powershell
.\build_windows.ps1
```

### Running Tests
```powershell
python -m pytest tests/
```

## Project Structure

- `app.py` - Main application entry point
- `ui/` - User interface components
- `tests/` - Test suite
- `tools/` - Build and release tools
- `requirements.txt` - Runtime dependencies
- `requirements-build.txt` - Build dependencies

## Version History

See CHANGES_*.txt files for detailed version history.

## License

See THIRD_PARTY.md for third-party licenses.
