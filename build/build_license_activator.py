"""
Скрипт сборки активатора лицензии в standalone exe через PyInstaller.
Собирает activate_license.py в exe файл, который можно запускать на компьютере рядом с БД.

Запуск из корня проекта: python build/build_license_activator.py
"""
import os
import sys
import subprocess
import time
import threading
import shutil
from datetime import timedelta

# Корень проекта (родитель папки build) и папка сборки
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BUILD_DIR)
# Подкаталоги внутри build/ для артефактов
DIST_DIR = os.path.join(BUILD_DIR, "dist")
# Путь к исходному файлу активации лицензии
ACTIVATE_LICENSE_SRC = os.path.join(PROJECT_ROOT, "tests/activate_license.py")
# Имя выходного exe файла
OUTPUT_EXE_NAME = "activate_license.exe"

# Настройка кодировки для Windows
try:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    import codecs
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

# Импорт логгера из корня проекта
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from logger.logger import py_logger


def format_duration(seconds):
    """Форматирует время выполнения в читаемый вид."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days}д {hours:02d}:{minutes:02d}:{secs:02d}"
    elif hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    elif minutes > 0:
        return f"{minutes:02d}:{secs:02d}"
    else:
        return f"{secs:02d}.{int((seconds % 1) * 100):02d}с" if seconds < 10 else f"{seconds:.0f}с"


class ProgressIndicator:
    """Анимация индикатора выполнения."""

    def __init__(self):
        self.running = False
        self.thread = None
        self.current_stage = ""
        self.start_time = None
        self.frames = ['-', '\\', '|', '/']

    def _animate(self):
        i = 0
        while self.running:
            elapsed = time.time() - self.start_time
            try:
                print(
                    f'\r{self.frames[i]} {self.current_stage} [{format_duration(elapsed)}]',
                    end='', flush=True
                )
            except UnicodeEncodeError:
                simple_frames = ['.', 'o', 'O']
                print(
                    f'\r{simple_frames[i % 3]} {self.current_stage} [{format_duration(elapsed)}]',
                    end='', flush=True
                )
            i = (i + 1) % len(self.frames)
            time.sleep(0.1)

    def start(self, stage_name: str):
        self.current_stage = stage_name
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print('\r' + ' ' * 100 + '\r', end='', flush=True)
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"✓ {self.current_stage} [{format_duration(elapsed)}]")


class CommandRunner:
    """Запуск команд с индикатором прогресса."""

    def __init__(self):
        self.progress = ProgressIndicator()

    def run(self, cmd: str, stage_name: str, cwd: str = None) -> bool:
        """Запускает команду с индикатором прогресса."""
        self.progress.start(stage_name)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or PROJECT_ROOT,
                capture_output=False,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            success = result.returncode == 0
            return success
        except Exception as e:
            py_logger.error(f"Ошибка выполнения команды: {e}")
            return False
        finally:
            self.progress.stop()


def check_prerequisites(builder_type: str = "pyinstaller"):
    """Проверка наличия необходимых файлов и зависимостей. builder_type: 'pyinstaller' или 'nuitka'."""
    py_logger.info("🔍 Проверка предварительных условий...")
    
    if not os.path.exists(ACTIVATE_LICENSE_SRC):
        py_logger.error(f"❌ Исходный файл не найден: {ACTIVATE_LICENSE_SRC}")
        return False
    
    py_logger.info(f"✅ Исходный файл найден: {ACTIVATE_LICENSE_SRC}")
    py_logger.info(f"🐍 Python версия: {sys.version}")
    
    runner = CommandRunner()
    if builder_type == "nuitka":
        try:
            import nuitka
            py_logger.info("✅ Nuitka найден")
        except ImportError:
            py_logger.warning("⚠️ Nuitka не найден, будет установлен автоматически")
            if not runner.run(f'"{sys.executable}" -m pip install nuitka', "Установка Nuitka"):
                py_logger.error("❌ Не удалось установить Nuitka")
                return False
    else:
        try:
            import PyInstaller
            py_logger.info(f"✅ PyInstaller найден: {PyInstaller.__version__}")
        except ImportError:
            py_logger.warning("⚠️ PyInstaller не найден, будет установлен автоматически")
            if not runner.run(f'"{sys.executable}" -m pip install pyinstaller', "Установка PyInstaller"):
                py_logger.error("❌ Не удалось установить PyInstaller")
                return False
    
    return True


def _get_icon_path():
    """Путь к иконке для exe. Создаёт icon.ico при первом запуске, если нужно."""
    icon_ico = os.path.join(BUILD_DIR, "icon.ico")
    if os.path.isfile(icon_ico):
        return icon_ico
    favicon = os.path.join(PROJECT_ROOT, "static", "favicon.ico")
    if os.path.isfile(favicon):
        return favicon
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "create_icon", os.path.join(BUILD_DIR, "create_icon.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if mod.create_ico_from_svg() or mod.create_simple_ico():
            return os.path.join(BUILD_DIR, "icon.ico")
    except Exception:
        pass
    return None


def build_with_pyinstaller():
    """Сборка активатора лицензии через PyInstaller."""
    runner = CommandRunner()
    
    # Создаем директории для выходных файлов
    os.makedirs(DIST_DIR, exist_ok=True)
    work_dir = os.path.join(BUILD_DIR, "work")
    spec_dir = BUILD_DIR
    
    # Получаем путь к иконке
    icon_path = _get_icon_path()
    icon_flag = ""
    if icon_path:
        icon_flag = f'--icon="{icon_path}" '
        py_logger.info(f"📌 Используется иконка: {icon_path}")
    
    # Путь к исходному файлу относительно корня проекта
    activate_license_rel = os.path.relpath(ACTIVATE_LICENSE_SRC, PROJECT_ROOT)
    
    # Команда сборки PyInstaller
    cmd = (
        f'"{sys.executable}" -m PyInstaller '
        '--console '
        '--onefile '
        '--clean '
        f'{icon_flag}'
        f'--distpath={os.path.join("build", "dist")} '
        f'--workpath={os.path.join("build", "work")} '
        f'--specpath={os.path.join("build")} '
        f'--name=activate_license '
        f'{activate_license_rel}'
    )
    
    success = runner.run(cmd, "Компиляция активатора лицензии (PyInstaller)", cwd=PROJECT_ROOT)
    
    if success:
        # PyInstaller создает exe с именем activate_license.exe в dist
        expected_exe = os.path.join(DIST_DIR, OUTPUT_EXE_NAME)
        if os.path.exists(expected_exe):
            py_logger.info(f"✅ Активатор лицензии успешно собран: {expected_exe}")
            py_logger.info(f"📦 Размер файла: {os.path.getsize(expected_exe) / (1024 * 1024):.2f} MB")
            return True
        else:
            # Ищем все exe файлы в dist
            exe_files = [f for f in os.listdir(DIST_DIR) if f.endswith('.exe')]
            if exe_files:
                actual_exe = os.path.join(DIST_DIR, exe_files[0])
                py_logger.info(f"✅ Активатор лицензии успешно собран: {actual_exe}")
                py_logger.info(f"📦 Размер файла: {os.path.getsize(actual_exe) / (1024 * 1024):.2f} MB")
                # Переименовываем в нужное имя, если отличается
                if exe_files[0] != OUTPUT_EXE_NAME:
                    target_path = os.path.join(DIST_DIR, OUTPUT_EXE_NAME)
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.rename(actual_exe, target_path)
                    py_logger.info(f"📝 Файл переименован в: {OUTPUT_EXE_NAME}")
                return True
            else:
                py_logger.error("❌ Exe файл не найден после сборки")
                return False
    
    return False


def build_with_nuitka() -> bool:
    """Сборка активатора лицензии через Nuitka."""
    runner = CommandRunner()
    os.makedirs(DIST_DIR, exist_ok=True)
    icon_path = _get_icon_path()
    icon_flag = ""
    if icon_path and sys.platform == "win32":
        icon_flag = f"--windows-icon-from-ico={icon_path.replace(chr(92), '/')} "
        py_logger.info(f"📌 Иконка: {icon_path}")
    activate_rel = os.path.relpath(ACTIVATE_LICENSE_SRC, PROJECT_ROOT).replace("\\", "/")
    out_dir = os.path.join("build", "dist").replace("\\", "/")
    cmd = (
        f'"{sys.executable}" -m nuitka '
        "--standalone --onefile --remove-output "
        f"--output-dir={out_dir} "
        "--assume-yes-for-downloads "
        "--output-filename=activate_license "
        f"{icon_flag}"
        f"{activate_rel}"
    )
    if sys.platform == "win32":
        cmd = "--mingw64 " + cmd
    success = runner.run(cmd, "Компиляция активатора лицензии (Nuitka)", cwd=PROJECT_ROOT)
    if success:
        exe_path = os.path.join(DIST_DIR, OUTPUT_EXE_NAME)
        if os.path.isfile(exe_path):
            py_logger.info(f"✅ Активатор собран: {exe_path}")
            return True
        py_logger.error("❌ exe не найден после сборки Nuitka")
    return False


def run_build(builder_type: str = "pyinstaller") -> bool:
    """Сборка активатора лицензии. builder_type: 'pyinstaller' или 'nuitka'. Вызывается из build.py при DEBUG."""
    if not check_prerequisites(builder_type):
        return False
    if builder_type == "nuitka":
        return build_with_nuitka()
    return build_with_pyinstaller()


def main():
    """Главная функция."""
    start_time = time.time()

    py_logger.info("=" * 60)
    py_logger.info("TS PIoT - Сборка активатора лицензии")
    py_logger.info("=" * 60)

    if not run_build():
        py_logger.error("❌ Сборка не удалась")
        sys.exit(1)

    elapsed = time.time() - start_time
    py_logger.info("\n" + "=" * 60)
    py_logger.info("✅ Сборка завершена успешно!")
    py_logger.info("=" * 60)
    py_logger.info(f"⏱ Время сборки: {format_duration(elapsed)}")
    py_logger.info(f"📁 Результат: {os.path.join(DIST_DIR, OUTPUT_EXE_NAME)}")
    py_logger.info("\n💡 Использование:")
    py_logger.info(f"   Скопируйте {OUTPUT_EXE_NAME} на компьютер рядом с БД")
    py_logger.info("   Запустите его для активации лицензии на текущем компьютере")
    py_logger.info("=" * 60)


if __name__ == "__main__":
    main()
