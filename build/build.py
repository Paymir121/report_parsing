"""
Скрипт сборки приложения. Все артефакты компиляции создаются в папке build/:
  build/dist/   — готовый exe и выход Nuitka/PyInstaller (и TS_PIoT_Setup.exe при --installer)
  build/work/   — рабочие файлы PyInstaller
  build/*.spec  — spec-файл PyInstaller (при использовании PyInstaller)

По умолчанию: PyInstaller. Nuitka: python build/build.py --builder nuitka.
Portable-сборка (один exe). С флагом --installer создаётся установочный файл
(Inno Setup): выбор пути установки, запись в реестр, удаление через «Программы и компоненты».

Запуск из корня проекта:
  python build/build.py                    — portable (PyInstaller)
  python build/build.py --builder nuitka   — portable (Nuitka)
  python build/build.py --installer         — portable + установочный exe
"""
import argparse
import os
import sys
import subprocess
import time
import threading
import shutil
from datetime import timedelta

# Корень проекта в sys.path до любых импортов из проекта (для GitLab Runner и др.)
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BUILD_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Имя файла БД по умолчанию (приложение создаёт при первом запуске, если нет)
DEFAULT_DB_FILE_NAME = "word_templates.db"

# Подкаталоги внутри build/ для артефактов
DIST_DIR = os.path.join(BUILD_DIR, "dist")
WORK_DIR = os.path.join(BUILD_DIR, "work")
# Пути относительно корня проекта (для вызовов Nuitka/PyInstaller с cwd=PROJECT_ROOT)
DIST_DIR_REL = os.path.join("build", "dist")
WORK_DIR_REL = os.path.join("build", "work")
SPEC_DIR_REL = "build"

# Кодировка вывода
try:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    import codecs
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

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
            py_logger.success(f"{self.current_stage} [{format_duration(elapsed)}]")


class CommandRunner:
    """Обертка для subprocess с логированием и прогрессом."""

    @staticmethod
    def run(cmd: str, description: str = "", cwd: str = None) -> bool:
        progress = ProgressIndicator()
        if description:
            progress.start(description + "...")
        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True, shell=True,
                encoding='utf-8', errors='replace', cwd=cwd
            )
            progress.stop()
            py_logger.info(f"✅ {description} завершено")
            return True
        except subprocess.CalledProcessError as e:
            progress.stop()
            py_logger.error(f"❌ Ошибка при {description.lower()}: {e}")
            if e.stderr:
                py_logger.info("Детали ошибки:")
                for line in e.stderr.split('\n'):
                    if line.strip():
                        py_logger.info(f"  {line}")
            if e.stdout:
                py_logger.info("Вывод компилятора:")
                for line in e.stdout.split('\n')[-10:]:
                    if line.strip():
                        py_logger.info(f"  {line}")
            return False
        except Exception as e:
            progress.stop()
            py_logger.error(f"❌ Неожиданная ошибка при {description.lower()}: {e}")
            return False


# Иконка: static/favicon.ico при наличии (exe и установщик)
FAVICON_ICO = os.path.join(PROJECT_ROOT, "static", "favicon.ico")
# Папка UI для копирования в dist (main_window.ui и др.)
UI_DIR = os.path.join(PROJECT_ROOT, "ui")


def _get_icon_path():
    """Путь к иконке для exe и установщика. Только static/favicon.ico."""
    if os.path.isfile(FAVICON_ICO):
        return os.path.normpath(os.path.abspath(FAVICON_ICO))
    return None


class BuildCleaner:
    """Удаляет старую сборку build/dist/"""

    @staticmethod
    def clean():
        py_logger.info("🧹 Очистка предыдущей сборки...")
        if os.path.exists(DIST_DIR):
            try:
                shutil.rmtree(DIST_DIR)
                py_logger.info(f"🗑 Папка '{DIST_DIR}' удалена")
            except PermissionError as e:
                py_logger.warning(f"⚠️ Не удалось удалить: {e}")
                for root, dirs, files in os.walk(DIST_DIR):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except PermissionError:
                            pass
        if os.path.exists(WORK_DIR):
            try:
                shutil.rmtree(WORK_DIR)
                py_logger.info(f"🗑 Папка '{WORK_DIR}' удалена")
            except PermissionError:
                pass
        os.makedirs(DIST_DIR, exist_ok=True)
        py_logger.info(f"📁 Создана папка сборки '{DIST_DIR}'")


class StaticFilesManager:
    """Копирует ui/ и опционально static/ и БД в папку с exe (build/dist/main/)."""

    PYINSTALLER_OUTPUT_DIR = "main"

    DB_FILE_NAME = DEFAULT_DB_FILE_NAME

    @classmethod
    def copy(cls):
        py_logger.info("📁 Копирование файлов в папку с exe...")
        dest_dir = os.path.join(DIST_DIR, cls.PYINSTALLER_OUTPUT_DIR)
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(UI_DIR):
            try:
                dest_ui = os.path.join(dest_dir, "ui")
                shutil.copytree(UI_DIR, dest_ui, dirs_exist_ok=True)
                py_logger.info(f"📦 ui скопирован в build/dist/{cls.PYINSTALLER_OUTPUT_DIR}/ui")
            except Exception as e:
                py_logger.error(f"❌ Ошибка копирования ui: {e}")
        else:
            py_logger.warning("⚠️ Папка ui не найдена")
        static_src = os.path.join(PROJECT_ROOT, "static")
        if os.path.exists(static_src):
            try:
                dest_static = os.path.join(dest_dir, "static")
                shutil.copytree(static_src, dest_static, dirs_exist_ok=True)
                py_logger.info(f"📦 static скопирован в build/dist/{cls.PYINSTALLER_OUTPUT_DIR}/static")
            except Exception as e:
                py_logger.error(f"❌ Ошибка копирования static: {e}")
        db_copied = False
        for db_candidate in [
            os.path.join(PROJECT_ROOT, "config", cls.DB_FILE_NAME),
            os.path.join(PROJECT_ROOT, cls.DB_FILE_NAME),
        ]:
            if os.path.isfile(db_candidate):
                try:
                    dest_db = os.path.join(dest_dir, cls.DB_FILE_NAME)
                    shutil.copy2(db_candidate, dest_db)
                    py_logger.info(f"📦 {cls.DB_FILE_NAME} скопирован в build/dist/{cls.PYINSTALLER_OUTPUT_DIR}/")
                    db_copied = True
                    break
                except Exception as e:
                    py_logger.error(f"❌ Ошибка копирования {cls.DB_FILE_NAME}: {e}")
        if not db_copied:
            py_logger.warning(f"⚠️ Файл {cls.DB_FILE_NAME} не найден (будет создан при первом запуске)")


class NuitkaBuilder:
    """Компиляция Python → exe через Nuitka."""

    def __init__(self, runner: CommandRunner):
        self.runner = runner

    def install(self):
        return self.runner.run(
            f'"{sys.executable}" -m pip install nuitka',
            "Установка Nuitka"
        )

    def install_ccache(self):
        return self.runner.run(
            f'"{sys.executable}" -m pip install ccache',
            "Установка ccache"
        )

    def build(self, use_mingw: bool = True) -> bool:
        win_flags = ""
        if sys.platform == "win32":
            if use_mingw:
                win_flags = "--mingw64 "
            else:
                win_flags = "--msvc=latest "
        win_meta = ""
        if sys.platform == "win32":
            win_meta = (
                "--windows-product-version=1.0.0.0 "
                "--windows-file-version=1.0.0.0 "
                "--windows-product-name=\"Word-шаблоны\" "
                "--windows-company-name=\"ReportParsing\" "
                "--windows-file-description=\"Word-шаблоны (Report Parsing)\" "
            )
        icon_flag = ""
        icon_path = _get_icon_path()
        if icon_path and sys.platform == "win32":
            icon_path_cmd = icon_path.replace("\\", "/")
            icon_flag = f"--windows-icon-from-ico={icon_path_cmd} "
            py_logger.info(f"📌 Иконка exe: {icon_path}")
        cmd = (
            f'"{sys.executable}" -m nuitka '
            f'{win_flags}'
            f'{win_meta}'
            f'{icon_flag}'
            '--standalone '
            '--onefile '
            '--remove-output '
            f'--output-dir={DIST_DIR_REL} '
            '--windows-console-mode=force '
            '--assume-yes-for-downloads '
            '--include-package-data=jinja2 '
            '--include-data-dir=ui=ui '
            '--include-data-dir=static=static '
            '--lto=no '
            '--jobs=2 '
            'main.py'
        )
        return self.runner.run(cmd, "Компиляция приложения (Nuitka)", cwd=PROJECT_ROOT)


def _write_pyinstaller_spec(icon_path: str = None):
    """Пишет main.spec в build/. Пути в datas задаются относительно каталога .spec (build/), иначе PyInstaller ищет build/ui и падает."""
    spec_path = os.path.join(BUILD_DIR, "main.spec")
    main_py = os.path.join(PROJECT_ROOT, "main.py")
    main_rel = os.path.relpath(main_py, BUILD_DIR).replace("\\", "/")
    icon_str = "None"
    icon_ico_in_build = os.path.join(BUILD_DIR, "icon.ico")
    if os.path.isfile(icon_ico_in_build):
        icon_str = repr(os.path.normpath(icon_ico_in_build))
    # Пути относительно каталога .spec (BUILD_DIR), чтобы PyInstaller находил ui/ в корне проекта
    ui_rel = os.path.relpath(UI_DIR, BUILD_DIR).replace("\\", "/")
    datas_list = f"[({repr(ui_rel)}, 'ui')]"
    static_dir = os.path.join(PROJECT_ROOT, "static")
    if os.path.isdir(static_dir):
        static_rel = os.path.relpath(static_dir, BUILD_DIR).replace("\\", "/")
        datas_list = f"[({repr(ui_rel)}, 'ui'), ({repr(static_rel)}, 'static')]"
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Сгенерировано build.py — icon задан строкой для корректной вставки в exe

a = Analysis(
    [{repr(main_rel)}],
    pathex=[{repr(PROJECT_ROOT)}],
    binaries=[],
    datas={datas_list},
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_str},
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
'''
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    return spec_path


class PyInstallerBuilder:
    """Сборка Python → exe через PyInstaller."""

    def __init__(self, runner: CommandRunner):
        self.runner = runner

    def install(self):
        return self.runner.run(
            f'"{sys.executable}" -m pip install pyinstaller',
            "Установка PyInstaller"
        )

    def build(self, use_mingw: bool = False) -> bool:
        # Копируем static/favicon.ico в build/icon.ico — PyInstaller надёжно встраивает иконку только если файл рядом со spec
        icon_src = _get_icon_path()
        if icon_src:
            dest_ico = os.path.join(BUILD_DIR, "icon.ico")
            try:
                os.makedirs(BUILD_DIR, exist_ok=True)
                shutil.copy2(icon_src, dest_ico)
                py_logger.info(f"📌 Иконка exe: {icon_src} → build/icon.ico")
            except Exception as e:
                py_logger.warning(f"⚠️ Не удалось скопировать иконку: {e}")
        _write_pyinstaller_spec()
        # При сборке по .spec нельзя передавать --specpath (только при генерации spec из main.py)
        cmd = (
            f'"{sys.executable}" -m PyInstaller '
            '--clean '
            f'--distpath={DIST_DIR_REL} '
            f'--workpath={WORK_DIR_REL} '
            f'"{os.path.join(SPEC_DIR_REL, "main.spec")}"'
        )
        return self.runner.run(cmd, "Компиляция приложения (PyInstaller)", cwd=PROJECT_ROOT)


def _normalize_dist_for_installer():
    """Приводит dist/ к единому виду для .iss: exe и файлы в dist/main/.
    Nuitka onefile даёт только dist/main.exe; static.copy() создаёт dist/main/ с static.
    Переносим main.exe в dist/main/. PyInstaller уже даёт dist/main/main.exe.
    """
    main_exe = os.path.join(DIST_DIR, "main.exe")
    main_dir = os.path.join(DIST_DIR, "main")
    if not os.path.isfile(main_exe):
        return
    if not os.path.isdir(main_dir):
        os.makedirs(main_dir, exist_ok=True)
    dest = os.path.join(main_dir, "main.exe")
    if os.path.abspath(dest) == os.path.abspath(main_exe):
        return
    try:
        shutil.copy2(main_exe, dest)
        os.remove(main_exe)
        py_logger.info("📁 Раскладка dist/ приведена к единому виду для установщика (main.exe → main/)")
    except Exception as e:
        py_logger.warning(f"⚠️ Не удалось перенести main.exe в main/: {e}")


def _find_iscc():
    """Ищет iscc.exe: PATH, затем Program Files\\Inno Setup 6 и 5."""
    if sys.platform != "win32":
        return None
    # 1) PATH (если добавлен вручную или через chocolatey)
    try:
        which = shutil.which("iscc")
        if which and os.path.isfile(which):
            return os.path.normpath(which)
    except Exception:
        pass
    # 2) Стандартные пути
    prog64 = os.environ.get("ProgramFiles", "C:\\Program Files")
    prog = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    for base in [prog64, prog]:
        iscc = os.path.join(base, "Inno Setup 6", "ISCC.exe")
        if os.path.isfile(iscc):
            return iscc
        iscc5 = os.path.join(base, "Inno Setup 5", "ISCC.exe")
        if os.path.isfile(iscc5):
            return iscc5
    return None


INNO_SETUP_DOWNLOAD_URL = "https://jrsoftware.org/isdl.php"


def _copy_installer_icon():
    """Копирует static/favicon.ico в build/favicon.ico для Inno Setup. Возвращает True при успехе."""
    src = os.path.join(PROJECT_ROOT, "static", "favicon.ico")
    dest = os.path.join(BUILD_DIR, "favicon.ico")
    if not os.path.isfile(src):
        py_logger.warning("Файл static/favicon.ico не найден — установщик будет использовать иконку по умолчанию.")
        return False
    try:
        os.makedirs(BUILD_DIR, exist_ok=True)
        shutil.copy2(src, dest)
        py_logger.info("Иконка для установщика: build/favicon.ico")
        return True
    except Exception as e:
        py_logger.error(f"Не удалось скопировать иконку в build/: {e}")
        return False


class InstallerBuilder:
    """Сборка установочного exe через Inno Setup (выбор пути, реестр, удаление)."""

    ISS_NAME = "build_installer.iss"

    def __init__(self, runner: CommandRunner):
        self.runner = runner

    def build(self) -> bool:
        iscc = _find_iscc()
        if not iscc:
            py_logger.error("Inno Setup не найден. Установите Inno Setup 6 и добавьте ISCC в PATH.")
            py_logger.info(f"Скачать: {INNO_SETUP_DOWNLOAD_URL}")
            py_logger.info("Ожидаемый путь: Program Files\\Inno Setup 6\\ISCC.exe")
            py_logger.info("CI/CD: choco install innosetup -y")
            return False
        iss_path = os.path.join(BUILD_DIR, self.ISS_NAME)
        if not os.path.isfile(iss_path):
            py_logger.error(f"Файл установщика не найден: {iss_path}")
            return False
        if not _copy_installer_icon():
            dest_ico = os.path.join(BUILD_DIR, "favicon.ico")
            if not os.path.isfile(dest_ico):
                py_logger.warning("build/favicon.ico отсутствует — в .iss укажите существующую иконку или уберите SetupIconFile.")
        iscc_quoted = iscc if iscc.find(" ") < 0 else f'"{iscc}"'
        iss_quoted = iss_path if iss_path.find(" ") < 0 else f'"{iss_path}"'
        cmd = f"{iscc_quoted} {iss_quoted}"
        return self.runner.run(cmd, "Сборка установочного файла (Inno Setup)", cwd=BUILD_DIR)


class BuildManager:
    """Оркестратор всех этапов сборки."""

    BUILDER_NUITKA = "nuitka"
    BUILDER_PYINSTALLER = "pyinstaller"

    def __init__(
        self,
        builder_type: str = BUILDER_NUITKA,
        use_mingw: bool = None,
        build_installer: bool = False,
    ):
        self.command_runner = CommandRunner()
        self.cleaner = BuildCleaner()
        self.static = StaticFilesManager()
        self._build_installer = build_installer
        if use_mingw is None:
            use_mingw = sys.platform == "win32" and builder_type != self.BUILDER_PYINSTALLER
        self._use_mingw = use_mingw
        if builder_type == self.BUILDER_PYINSTALLER:
            self.builder = PyInstallerBuilder(self.command_runner)
            self.builder_name = "PyInstaller"
        else:
            self.builder = NuitkaBuilder(self.command_runner)
            self.builder_name = "Nuitka"

    def check_environment(self):
        py_logger.info("🔍 Проверка окружения...")
        py_logger.info(f"🐍 Python версия: {sys.version}")
        py_logger.info(f"📁 Папка сборки: {BUILD_DIR}")
        try:
            result = subprocess.run(
                'where cl.exe' if os.name == 'nt' else 'which gcc',
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                py_logger.info("✅ Компилятор найден")
            else:
                py_logger.warning("⚠️ Компилятор не найден")
        except Exception:
            py_logger.warning("⚠️ Не удалось проверить компилятор")

    def run(self):
        start_time = time.time()
        py_logger.info(f"🚀 Начало сборки ({self.builder_name})\n" + "=" * 60)
        self.check_environment()
        self.cleaner.clean()
        if not self.builder.install():
            py_logger.error(f"❌ Не удалось установить {self.builder_name}")
            return
        if self.builder_name == "Nuitka" and hasattr(self.builder, "install_ccache"):
            if not self.builder.install_ccache():
                py_logger.warning("⚠️ Не удалось установить ccache, продолжаем...")
        use_mingw = getattr(self, "_use_mingw", True)
        if not self.builder.build(use_mingw=use_mingw):
            if self.builder_name == "Nuitka" and use_mingw:
                py_logger.warning("🔄 Повтор с MSVC (--msvc)...")
                if self.builder.build(use_mingw=False):
                    pass
                else:
                    py_logger.warning("🔄 Сборка не удалась")
            else:
                py_logger.warning("🔄 Сборка не удалась")
        self.static.copy()
        if self._build_installer and sys.platform == "win32":
            _normalize_dist_for_installer()
            installer_builder = InstallerBuilder(self.command_runner)
            if not installer_builder.build():
                py_logger.warning("⚠️ Сборка установщика не выполнена")
            else:
                setup_exe = os.path.join(DIST_DIR, "ReportParsing_Setup.exe")
                if os.path.isfile(setup_exe):
                    root_dist = os.path.join(PROJECT_ROOT, "dist")
                    os.makedirs(root_dist, exist_ok=True)
                    dest_setup = os.path.join(root_dist, "ReportParsing_Setup.exe")
                    try:
                        shutil.copy2(setup_exe, dest_setup)
                        py_logger.info(f"📦 Установщик: {DIST_DIR}")
                        py_logger.info(f"📦 Копия в корень: {dest_setup}")
                    except Exception as e:
                        py_logger.warning(f"Не удалось скопировать установщик в dist/: {e}")
                        py_logger.info(f"📦 Установщик: {setup_exe}")
                else:
                    py_logger.warning("Файл ReportParsing_Setup.exe не найден после сборки Inno Setup.")
        if sys.platform == "win32":
            try:
                import settings as _st
                if getattr(_st, "DEBUG", False):
                    import importlib.util
                    act_path = os.path.join(BUILD_DIR, "build_license_activator.py")
                    if os.path.isfile(act_path):
                        spec = importlib.util.spec_from_file_location("build_license_activator", act_path)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        py_logger.info("Сборка активатора лицензии (DEBUG)...")
                        if mod.run_build(builder_type=self.builder_name):
                            act_exe = os.path.join(DIST_DIR, "activate_license.exe")
                            if os.path.isfile(act_exe):
                                root_dist = os.path.join(PROJECT_ROOT, "dist")
                                os.makedirs(root_dist, exist_ok=True)
                                try:
                                    shutil.copy2(act_exe, os.path.join(root_dist, "activate_license.exe"))
                                    py_logger.info("Активатор лицензии: build/dist/ и dist/activate_license.exe")
                                except Exception as e:
                                    py_logger.warning(f"Не удалось скопировать activate_license.exe в dist/: {e}")
                        else:
                            py_logger.warning("Сборка активатора лицензии не выполнена.")
            except Exception:
                pass
        py_logger.info("\n" + "=" * 60)
        py_logger.success("🎉 Сборка завершена!")
        py_logger.complete(f"⏱ Время: {format_duration(time.time() - start_time)}")
        py_logger.info(f"📁 Результат: {DIST_DIR}")
        if self._build_installer and sys.platform == "win32" and os.path.isdir(os.path.join(PROJECT_ROOT, "dist")):
            py_logger.info(f"📁 Установщик также: {os.path.join(PROJECT_ROOT, 'dist')}")
        if sys.platform == "win32":
            if self.builder_name == "Nuitka":
                py_logger.info("")
                py_logger.info("Если Windows блокирует exe («не удалось проверить издателя»):")
                py_logger.info("  1. ПКМ по exe → Свойства → внизу «Разблокировать» → ОК")
                py_logger.info("  2. Или в окне блокировки: «Подробнее» → «Всё равно выполнить»")
            py_logger.info("")
            py_logger.info("Если иконка exe не обновилась: Windows кэширует иконки. Перезапустите проводник (ПКМ по панели задач → Выйти из проводника, затем Файл → Выполнить → explorer) или перезагрузите ПК.")


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Сборка приложения: по умолчанию portable (один exe). С флагом --installer — установочный файл."
    )
    parser.add_argument(
        "--installer",
        action="store_true",
        default=False,
        help="После сборки создать установочный exe (Inno Setup). По умолчанию — только portable.",
    )
    parser.add_argument(
        "--no-installer",
        action="store_false",
        dest="installer",
        help="Собрать только portable exe без установщика",
    )
    parser.add_argument(
        "--builder",
        choices=[BuildManager.BUILDER_NUITKA, BuildManager.BUILDER_PYINSTALLER],
        default=BuildManager.BUILDER_PYINSTALLER,
        help="Инструмент сборки (по умолчанию: pyinstaller)",
    )
    parser.add_argument(
        "--no-mingw",
        action="store_true",
        help="Использовать MSVC вместо MinGW64 (только Nuitka)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    use_mingw = not args.no_mingw

    try:
        BuildManager(
            builder_type=args.builder,
            use_mingw=use_mingw,
            build_installer=args.installer,
        ).run()
    except KeyboardInterrupt:
        py_logger.warning("⏹ Сборка прервана пользователем")
    except Exception as e:
        py_logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        py_logger.complete("=" * 60)
