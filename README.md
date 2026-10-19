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
Enabled frames are overlaid at the source scale and position without detecting
existing frames. Disabled frames leave the source drawing unchanged. Long title fields wrap inside their cells.

Set the stage, reviewer and norm-control signer in the system settings. These
reviewers apply automatically to every drawing in the system. Select the developer
explicitly for each drawing; neither the system nor the execution supplies a default.
A drawing can override the stage and has separate number and name fields in its preview
card. Both title-block and attachment dates come from the linked АОСР.
Shared framed drawings export separately for each linked act, using that act's
selected sheets and attachment details. Export warns about empty signer cells
and allows returning to the cards or continuing with those cells empty.

### Ведомость объёмов работ к АОСР

В карточке АОСР откройте вкладку «Объёмы работ»: включите ведомость и
заполните одну или несколько строк (работа, место, единица, количество).
Количество допускает десятичную запятую. Расчёты автоматически не выполняются.
Переключатель действует только на этот акт; для АООК ведомость не создаётся.

Файл формируется по встроенному шаблону. Свой DOCX можно выбрать в разделе
«Профили и шаблоны → Ведомость объёмов работ», отдельно для объекта/профиля.
Строка таблицы с тегами `{{Объемы.Номер}}`, `{{Объемы.Наименование}}`,
`{{Объемы.Место}}`, `{{Объемы.Единица}}`, `{{Объемы.Количество}}`
повторяется для каждого объёма. Кнопка «Создать образец с тегами» выдаёт
встроенный редактируемый шаблон. Для преобразования DOCX в PDF нужен Word.

Ведомость располагается сразу после АОСР, перед фототаблицей. Её фактическое
число листов подставляется в список приложений акта и учитывается в реестре.
«Составил» — подписант №5 акта (лицо, выполнившее работы), «Проверил» —
подписант №3 (строительный контроль лица, осуществляющего строительство).
Кнопка «Скачать ведомость DOCX» сохраняет её отдельно.

### История и конфликты карточек

Кнопка «История версий» в карточке открывает линию сохранений с датой,
пользователем, компьютером и перечнем изменённых полей. Все карточки, включая
документы без отдельного экрана, доступны через «Синхронизация → История всех
карточек». История относится только к самой карточке: восстановление объекта
или системы не откатывает вложенные акты и другие дочерние карточки.
История сохраняет собственные поля и файлы карточки. Связанные справочники
и документы имеют отдельную историю; при просмотре формы их реквизиты
берутся из текущих справочников.

«Посмотреть» открывает прошлое состояние только для чтения с вложениями и
сравнением полей. Рабочие данные при просмотре не меняются. «Восстановить»
создаёт новую запись с прежним содержимым; к более поздней версии можно
вернуться таким же способом. Файлы для просмотра открываются во временной
копии вне базы, чтобы Word или другой редактор не изменил исторический файл.

При конфликте сохраняется любое количество вариантов. Карточка блокируется
до выбора пользователем итоговой версии. Любой пользователь может выполнить
выбор, решение записывается с родителями всех текущих веток. Если позже
приходит новая независимая офлайн ветка, она также сохраняется и требует
нового выбора. Сохранённый конфликт не препятствует работе с другими
карточками и закрытию приложения.

В каждой папке карточки находится «История версий/Версия 000001_<ID>».
Внутри — «Версия.json» с данными карточки, автором, временем, родителями и
списком вложений. Новый или заменённый PDF/Word/фото записывается в папку
первой версии, использующей это содержимое. Неизменённые файлы в последующих
версиях не дублируются. При независимых офлайн изменениях номера могут
совпасть; уникальный ID отличает ветки и предотвращает перезапись папок.

В истории можно отметить несколько прошлых версий и удалить их. Перед
удалением показывается оценка освобождаемого места. Текущие и неразрешённые
варианты защищены. Если вложение удаляемой версии используется оставшейся,
оно сначала переносится в её папку. Ненужные файлы и записи удаляются, а
короткие отметки об удалении и связях версий остаются для обмена через
Яндекс Диск. Ручные резервные копии сохраняют свои файлы: удаление истории
не уничтожает данные явно созданных копий. Автоматически хранится один
актуальный снимок всей базы, а откат отдельных карточек обеспечивает история.

Удаляйте версии через приложение. При неполной доставке версии или её
файлов отображается ожидание синхронизации; восстановление без необходимых
файлов запрещено. Яндекс Диск должен хранить всю папку базы локально на
каждом ПК. Это файловый обмен без сервера, поэтому программа не может
подтвердить доставку на выключенный или отключённый компьютер. Переносимый
ZIP содержит выбранный рабочий комплект, а не полную историю исходной базы.

### Приложения к АОСР в экспорте

В профиле заказчика, в разделе «Приложения к АОСР», выберите расположение
схем: после соответствующего АОСР (по умолчанию) или общим разделом.
При размещении после акта комплект идёт блоками: АОСР, его приложения,
следующий АОСР. Порядок схем, фототаблиц и документов качества меняется
стрелками в профиле. Ведомость объёмов, если включена, остаётся сразу после
АОСР. Для применения профиля выберите «По профилю заказчика» на странице сборки.

Схемы, связанные с АОСР, включаются с выбранными диапазонами листов и рамками
этого акта. Общие схемы без связи с АОСР остаются в разделе схем. Повторение
сертификатов регулируется настройкой «Паспорта и сертификаты»: один раз,
у первого акта или после каждого акта. В предпросмотре показан каждый
включённый документ, включая сертификаты; число страниц здесь оценочное.
Итоговый реестр рассчитывается по фактическим страницам PDF.

При сохранении повторно используются расчёты путей карточек; неизменившиеся
проекции истории не перечитываются. Внутри одного экспорта общий исходный
PDF разбирается один раз, а диапазоны листов и рамки применяются отдельно
для каждого использования. При переходах по вкладкам индекс файлов
переиспользуется до следующего изменения или получения обновлённых данных.
