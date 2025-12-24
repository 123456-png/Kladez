import os
import sys
import subprocess
import webbrowser
from time import sleep


def setup_django_environment():
    """Настраивает окружение Django для работы в EXE"""

    # Получаем базовую директорию
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    project_dir = os.path.join(base_dir, "Kladez")

    # Добавляем пути в sys.path чтобы Django мог найти модули
    sys.path.insert(0, project_dir)  # Папка с manage.py
    sys.path.insert(0, os.path.join(project_dir, "Kladez"))  # Папка с настройками
    sys.path.insert(0, os.path.join(project_dir, "kladez_app"))  # Папка приложения

    # Устанавливаем переменную окружения
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Kladez.settings')

    return project_dir


def main():
    print("=" * 50)
    print("    ЗАПУСК КЛАДЕЗЬ - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("=" * 50)

    # Настраиваем окружение Django
    project_dir = setup_django_environment()

    print(f"Project dir: {project_dir}")
    print(f"sys.path: {sys.path}")

    # Переходим в директорию проекта
    os.chdir(project_dir)
    print(f"Текущая директория: {os.getcwd()}")

    # Проверяем manage.py
    if not os.path.exists("manage.py"):
        print("✗ manage.py не найден!")
        input("Нажмите Enter для выхода...")
        return

    print("✓ manage.py найден")

    # Проверяем настройки Django
    print("Проверка настроек Django...")
    try:
        import django
        from django.conf import settings

        if not settings.configured:
            django.setup()

        print("✓ Django настройки загружены")

    except Exception as e:
        print(f"✗ Ошибка настройки Django: {e}")
        print("Пробуем альтернативный подход...")

        # Альтернативный подход - запускаем через subprocess
        try:
            result = subprocess.run(
                [sys.executable, "manage.py", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✓ Django проверка пройдена через subprocess")
            else:
                print(f"✗ Django проверка не пройдена: {result.stderr}")
        except Exception as e2:
            print(f"✗ Ошибка при проверке Django: {e2}")

        input("Нажмите Enter для выхода...")
        return

    # Создаём базу данных если нужно
    if not os.path.exists('db.sqlite3'):
        print("Создание базы данных...")
        try:
            result = subprocess.run(
                [sys.executable, "manage.py", "migrate"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print("✓ Миграции применены")

                # Создаём суперпользователя
                result = subprocess.run(
                    [sys.executable, "-c",
                     "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Kladez.settings'); "
                     "import django; django.setup(); "
                     "from django.contrib.auth.models import User; "
                     "User.objects.create_superuser('admin', '', 'admin')"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✓ Администратор создан: логин - admin, пароль - admin")
                else:
                    print(f"⚠ Администратор не создан: {result.stderr}")
            else:
                print(f"✗ Ошибка миграций: {result.stderr}")
        except Exception as e:
            print(f"✗ Ошибка при создании БД: {e}")

    # Запускаем сервер
    print("Запуск сервера...")

    try:
        # Запускаем сервер
        process = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", "8000", "--noreload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        print("Сервер запущен, ждём 5 секунд...")
        sleep(5)

        webbrowser.open("http://localhost:8000")
        print("Браузер открыт: http://localhost:8000")

        print("=" * 50)
        print("ВЫВОД СЕРВЕРА:")
        print("=" * 50)

        # Читаем вывод построчно
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()

        returncode = process.wait()
        print(f"Сервер завершился с кодом: {returncode}")

    except KeyboardInterrupt:
        print("Остановка по Ctrl+C...")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"Ошибка: {e}")

    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()