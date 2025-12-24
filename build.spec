pyinstaller --onefile --console ^
--name "Kladez" ^
--add-data "Kladez\Kladez;Kladez" ^
--add-data "Kladez\kladez_app;kladez_app" ^
--add-data "Kladez\kladez_app\templates;templates" ^
--add-data "Kladez\manage.py;." ^
--hidden-import=django.core.management ^
--hidden-import=django.db.backends.sqlite3 ^
--hidden-import=kladez_app.apps ^
--hidden-import=kladez_app.models ^
app.py
