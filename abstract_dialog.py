from typing import Any

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt

from logger.logger import py_logger, error_logger
from ui_file_loader import UiFileLoader
from path_handler import PathHandler


# class AbstractDialog(QDialog):
class AbstractDialog:
    """
    Абстрактный класс для окон созданого в Qt Designer. При закрытии окна сохраняет местоположение и геометрию в QSettings.
    Можно переопределить методы init_ui и init_connect в дочернем классе при наличии потребности в этом.
    """
    def __init__(
        self,
        ui_file_name: str,
        use_ui_subfolder: bool = True,
        dots_in_path: int = 1,
        class_of_main_window: Any = None,
        open_as_modal: bool = True,
        window_title: str = None,
        enable_tree_widget: bool = False,
        move_to_bottom_right: bool = False,
        delete_on_close: bool = True,
        show_full_screen: bool = False,
    ):
        super().__init__()
        self.name_dialog = self.__class__.__name__
        self.dots_in_path: int = dots_in_path

        if class_of_main_window is not None:
            from main_window_class import MainWindow
            self.class_of_main_window: MainWindow = class_of_main_window
            parent_class = self.class_of_main_window.window
        else:
            parent_class = None
            self.class_of_main_window = class_of_main_window

        from settings import app_settings
        self.app_settings = app_settings

        self.path_handler = PathHandler(
            file_name=ui_file_name,
            dots_in_path=dots_in_path,
            use_ui_subfolder=use_ui_subfolder,
        )
        self.window: QDialog = UiFileLoader(
            ui_file_path=self.path_handler.file_path,
            parent=parent_class,
        ).load(QDialog)


        # self.window.setModal(True)
        # self.window.raise_()
        # self.window.activateWindow()
        # self.window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)


        self.window.rejected.connect(
            self.handle_window_closing
            # -----------------------
            # lambda:
            # self.handle_window_closing(
            # )
        )

        # self.move_to_bottom_right()
        # =========================
        if move_to_bottom_right:
            self.move_to_bottom_right()
        else:
            self.window.move(
                int(self.app_settings.value(f"{self.name_dialog}_x", 0)),
                int(self.app_settings.value(f"{self.name_dialog}_y", 0)),
            )

        py_logger.info(f"AD.1: {self.name_dialog} window loaded")

        self.enable_tree_widget: bool = enable_tree_widget

        self.init_ui()
        self.init_connect()

        self.window.setWindowTitle(
            window_title if window_title else self.name_dialog,
        )

        if open_as_modal:
            self.window.open()
        else:
            self.window.show()

        if show_full_screen:
            self.window.showFullScreen()
        # else:
        #     self.window.setGeometry(
        #         self.window.screen().availableGeometry()
        #     )

        if delete_on_close:
            self.window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # self.window.setWindowModality(Qt.WindowModality.ApplicationModal)
        # ------------------------
        # self.window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        py_logger.info(f"AD.2: {self.name_dialog} window loaded")


    def init_ui(self):
        pass

    def init_connect(self):
        pass

    @error_logger()
    def move_to_bottom_right(self):
        # :: !!!!!!! РАЗМЕРЫ "ОКНА" / "ЭКРАНА" (РАЗМЕРЫ ОКНА / РАЗМЕРЫ ЭКРАНА) !!!!!!!
        screen_geometry = self.window.screen().availableGeometry()
        # screen_geometry = self.window.screen().geometry()

        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        widget_width = self.window.frameGeometry().width()
        widget_height = self.window.frameGeometry().height()
        # Позиционирование виджета в правом нижнем углу
        # TODO убрать хардкод. Использовать геометрию экрана и узнать ширину полоски виндового меню
        self.window.move(
            self.app_settings.value(f"{self.name_dialog}_x", screen_width - widget_width - 70),
            self.app_settings.value(f"{self.name_dialog}_y", screen_height - widget_height - 80)
        )

    @error_logger()
    def handle_window_closing(
        self,
    ):
        py_logger.info(f"AD.2: Закрывается окно '{self.name_dialog}'...")
        self.app_settings.setValue(f"{self.name_dialog}_size", self.window.size())
        self.app_settings.setValue(f"{self.name_dialog}_x", self.window.x())
        self.app_settings.setValue(f"{self.name_dialog}_y", self.window.y())
        try:
            if self.class_of_main_window.window.isVisible():
                self.app_settings.setValue(f"{self.name_dialog}_viewer", False)
        except Exception as error:
            py_logger.error(f"AD.3: Error = {error}")

        py_logger.info(f"AD.4: self.window = {self.window}")


    # # def installEventFilter(self, filterObj):
    # def installEventFilter(
    #     self,
    #     filterObj: QObject,
    #     **kwargs,
    # ):
    #     super().installEventFilter(filterObj)


    # def eventFilter(self, watched, event: QEvent) -> bool:
    """
    def eventFilter(self,
                arg__1: QObject,
                arg__2: QEvent) -> bool
    """
    """
    eventFilter(self, watched: PySide6.QtCore. QObject, event: PySide6.QtCore. QEvent) -> bool
    """
    # def eventFilter(self, arg__1, arg__2):
    # ==========================================
    """
    def eventFilter(
        self,
        watched: QObject,
        event: QEvent,
        **kwargs,
    ):
    # ) -> bool:
        super().eventFilter(watched, event)
    """
    # ==========================================
    # :: 012
    """
    def eventFilter(
        self,
        source: QObject,
        event: QEvent,
        # **kwargs,
    # ):
    ) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            print("4: focusInEvent =", source.objectName())
        elif event.type() == QEvent.Type.FocusOut:
            print("4: focusOutEvent =", source.objectName())
        return super().eventFilter(source, event)
        # return True
    """
