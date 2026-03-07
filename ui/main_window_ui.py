# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 560)
        MainWindow.setMinimumSize(QSize(640, 400))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.mainLayout = QVBoxLayout(self.centralwidget)
        self.mainLayout.setSpacing(10)
        self.mainLayout.setObjectName(u"mainLayout")
        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setSpacing(8)
        self.toolbarLayout.setObjectName(u"toolbarLayout")
        self.add_file_pushbutton = QPushButton(self.centralwidget)
        self.add_file_pushbutton.setObjectName(u"add_file_pushbutton")
        self.add_file_pushbutton.setMinimumWidth(140)

        self.toolbarLayout.addWidget(self.add_file_pushbutton)

        self.label_template = QLabel(self.centralwidget)
        self.label_template.setObjectName(u"label_template")
        self.label_template.setMinimumSize(QSize(60, 0))

        self.toolbarLayout.addWidget(self.label_template)

        self.tables_combobox = QComboBox(self.centralwidget)
        self.tables_combobox.setObjectName(u"tables_combobox")
        self.tables_combobox.setMinimumWidth(220)

        self.toolbarLayout.addWidget(self.tables_combobox)

        self.load_excel_pushbutton = QPushButton(self.centralwidget)
        self.load_excel_pushbutton.setObjectName(u"load_excel_pushbutton")
        self.load_excel_pushbutton.setMinimumWidth(140)
        self.load_excel_pushbutton.setEnabled(False)

        self.toolbarLayout.addWidget(self.load_excel_pushbutton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toolbarLayout.addItem(self.horizontalSpacer)


        self.mainLayout.addLayout(self.toolbarLayout)

        self.groupBox_fields = QGroupBox(self.centralwidget)
        self.groupBox_fields.setObjectName(u"groupBox_fields")
        self.groupBox_fields.setMinimumHeight(200)
        self.groupBoxLayout = QVBoxLayout(self.groupBox_fields)
        self.groupBoxLayout.setObjectName(u"groupBoxLayout")
        self.data_tables = QTableWidget(self.groupBox_fields)
        if (self.data_tables.columnCount() < 2):
            self.data_tables.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.data_tables.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.data_tables.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.data_tables.setObjectName(u"data_tables")
        self.data_tables.setColumnCount(2)
        self.data_tables.setRowCount(0)
        self.data_tables.setHorizontalHeaderStretchLastSection(True)
        self.data_tables.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.groupBoxLayout.addWidget(self.data_tables)


        self.mainLayout.addWidget(self.groupBox_fields)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setObjectName(u"bottomLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottomLayout.addItem(self.horizontalSpacer_2)

        self.export_pushbutton = QPushButton(self.centralwidget)
        self.export_pushbutton.setObjectName(u"export_pushbutton")
        self.export_pushbutton.setMinimumWidth(180)
        self.export_pushbutton.setMinimumHeight(32)

        self.bottomLayout.addWidget(self.export_pushbutton)


        self.mainLayout.addLayout(self.bottomLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Word-\u0448\u0430\u0431\u043b\u043e\u043d\u044b", None))
        self.add_file_pushbutton.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0448\u0430\u0431\u043b\u043e\u043d\u2026", None))
        self.label_template.setText(QCoreApplication.translate("MainWindow", u"\u0428\u0430\u0431\u043b\u043e\u043d:", None))
        self.load_excel_pushbutton.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0438\u0437 Excel\u2026", None))
        self.groupBox_fields.setTitle(QCoreApplication.translate("MainWindow", u"\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u044f \u043f\u043e\u043b\u0435\u0439 \u0448\u0430\u0431\u043b\u043e\u043d\u0430", None))
        ___qtablewidgetitem = self.data_tables.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u043b\u0435", None));
        ___qtablewidgetitem1 = self.data_tables.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435", None));
        self.export_pushbutton.setText(QCoreApplication.translate("MainWindow", u"\u0421\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442", None))
    # retranslateUi

