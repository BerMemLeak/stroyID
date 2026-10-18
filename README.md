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

## Document workflow in 0.9.5

Card fields save automatically after a short pause. Navigation, deletion and
export wait for pending writes. Creation dialogs still require an explicit
Create/Save action. A failed write leaves the entered data available for retry.

A quality document can be shared by multiple materials. Use **Добавить документ**
or **Выбрать существующий** in a material card; **Отвязать** removes only that
material's link. Existing private documents can be shared through their editor.

On the assembly page, select the issuing company, customer, export profile or
custom order, and whether to include common and operational documentation.
Drag a handle to reorder sections/documents; Alt + Up/Down is also supported.
Company selection changes generated documents without changing the object card.

HTML drawing frames are configured in **Профили и шаблоны → Исполнительные схемы**.
Frames require the ISOCPEUR font; the same section can check availability and
load a font file. The font is not bundled. Original drawing PDFs are preserved.
The reference uses ГОСТ Р 21.101-2026, appendices Е and Ж; the total sheet count
is shown on the first sheet only. Sources checked:
[Rosstandart record](https://protect.gost.ru/gost/details/17bc12e8-6579-4145-b141-56855e772e7f)
and the published standard's form 3 and clause Е.1.

The supplied Word title and registry examples are available from their template
sections. A title can use `{{Логотип_Компании}}`; titles without that tag receive
the selected company's logo at the top right.

`python tools/build_release.py` runs the unit tests, real Qt integration checks,
PyInstaller packaging and an isolated executable self-test. Windows builds are
also checked by `.github/workflows/build-windows.yml`. Linux build evidence is
in `validation/0.9.5-linux`; Microsoft Word COM conversion requires Windows and
is not executed by the Linux validation.


### Drawing frames from the ВК1 reference

The built-in title block follows the supplied ВК1 example. Every sheet shows
its source PDF sheet number, total sheets and the linked act attachment block.
Imported drawings fit between the attachment block and title block at their
original page size. Long title fields wrap inside their cells.

Set the stage, reviewer and norm-control signer in the system settings. These
reviewers apply automatically to every drawing in the system. Select the developer
explicitly for each drawing; neither the system nor the execution supplies a default.
A drawing can override the stage and has separate number and name fields in its preview
card. Both title-block and attachment dates come from the linked АОСР.
Shared framed drawings export separately for each linked act, using that act's
selected sheets and attachment details. Export warns about empty signer cells
and allows returning to the cards or continuing with those cells empty.
