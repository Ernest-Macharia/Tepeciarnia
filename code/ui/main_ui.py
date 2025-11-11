# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1070, 900)
        MainWindow.setMinimumSize(QSize(0, 900))
        MainWindow.setStyleSheet(u"/* Gradient background and modern rounded look */\n"
"QWidget#centralwidget {\n"
"  background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(59, 130, 246, 255), stop:0.6 rgba(99, 102, 241, 255), stop:1 rgba(99, 102, 241, 255));\n"
"}\n"
"\n"
"QFrame#uploadArea {\n"
"  border: 2px dashed rgba(255, 255, 255, 0.12);\n"
"  border-radius: 12px;\n"
"  background: transparent;\n"
"}\n"
"\n"
"QFrame#uploadArea:hover {\n"
"  background: rgba(255, 255, 255, 0.04);\n"
"}\n"
"\n"
"QFrame#card {\n"
"  background: rgba(255, 255, 255, 0.06);\n"
"  border-radius: 16px;\n"
"  border: 1px solid rgba(255, 255, 255, 0.12);\n"
"}\n"
"\n"
"QPushButton {\n"
"  border-radius: 12px;\n"
"  padding: 8px 12px;\n"
"\n"
"}\n"
"\n"
"QPushButton.aactive {\n"
"  background: white;\n"
"  color: #1e40af;\n"
"  font-weight: 600;\n"
"}\n"
"\n"
"QPushButton.primary {\n"
"  background: white;\n"
"  color: #1e40af;\n"
"  font-weight: 600;\n"
"}\n"
"\n"
"QPushButton.danger {\n"
"  background: transparent;\n"
"  color: white;\n"
"  "
                        "font-weight: 600;\n"
"  border: 2px solid  rgb(248, 68, 68);\n"
"}\n"
"QPushButton.danger:hover {\n"
"  background: rgb(248, 68, 68);\n"
"  border: 2px solid  rgb(248, 68, 68);\n"
"}\n"
"\n"
"QPushButton.deactive {\n"
"  background: transparent;\n"
"  color: white;\n"
"  border: 1px solid rgba(255, 255, 255, 0.18);\n"
"}\n"
"\n"
"QPushButton.deactive:hover {\n"
"  color: white;\n"
"  border: 1px solid rgba(255, 255, 255, 0.2);\n"
"  background-color: rgba(255, 255, 255, 0.2);\n"
"}\n"
"\n"
"QPushButton.ghost:hover {\n"
"  border: 1px solid rgba(255, 255, 255, 0.2);\n"
"  background-color: rgba(255, 255, 255, 0.2);\n"
"}\n"
"\n"
"QPushButton.ghost {\n"
"  color: white;\n"
"  background-color: transparent;\n"
"  border: 1px solid rgba(255, 255, 255, 0.2);\n"
"}\n"
"\n"
"QLineEdit,\n"
"QComboBox,\n"
"QSpinBox {\n"
"  background: rgba(255, 255, 255, 0.06);\n"
"  border: 1px solid rgba(255, 255, 255, 0.12);\n"
"  border-radius: 10px;\n"
"  padding: 6px 8px;\n"
"  color: white;\n"
"}\n"
"\n"
"QLabel {\n"
"  color: w"
                        "hite;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"  border: 2px solid rgba(255, 255, 255, 0.795);\n"
"}\n"
"\n"
"QLabel#autoLabel {\n"
"  padding-left: 2px;\n"
"}\n"
"\n"
"/* QLineEdit#emailInput,QLineEdit#passwordInput{\n"
"  padding: 12px;\n"
"} */\n"
"\n"
"/* Targets the QLabel acting as the logo container */\n"
"QLabel#logoLabel {\n"
"  /* Set the size of the icon within the QLabel */\n"
"  icon-size: 32px 32px;\n"
"  /* Set the color for the SVG (this overrides fill=\"currentColor\") */\n"
"  color: #f5f6fa;\n"
"  /* Bright white/near-white */\n"
"\n"
"  /* Set the dynamic property defined in Designer as the actual icon source */\n"
"  /* qproperty-icon: url(:/icons/logo_biale.svg);  */\n"
"\n"
"  /* Padding to create breathing room around the logo */\n"
"  padding: 5px;\n"
"  margin-right: 15px;\n"
"}\n"
"\n"
"/* Add a subtle hover effect if the logo is clickable */\n"
"QLabel#appLogoLabel:hover {\n"
"  color: #3498db;\n"
"  /* Change logo color to blue on hover */\n"
"}\n"
"\n"
"/* Load the white icon by defau"
                        "lt\n"
"QToolButton#timerButton {\n"
"    icon-size: 24px 24px;\n"
"    qproperty-icon: url(assets/timer_white.png);\n"
"    background-color: transparent;\n"
"}\n"
"\n"
"Load the blue icon when hovering\n"
"QToolButton#timerButton:hover {\n"
"    qproperty-icon: url(assets/timer_blue.png);\n"
"    background-color: #34495e;\n"
"    border-radius: 5px;\n"
"} */\n"
"\n"
"\n"
"/* ----------------------------------------------------\n"
"   QCheckBox BASE STYLES\n"
"   ---------------------------------------------------- */\n"
"\n"
"QCheckBox {\n"
"  /* Base text color for the checkbox label */\n"
"  color: #f5f6fa;\n"
"\n"
"  /* Add padding/margin for spacing, especially when used in a layout */\n"
"  padding: 5px;\n"
"  spacing: 8px;\n"
"  /* Space between the box and the text label */\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"  /* Define the size of the clickable box area */\n"
"  width: 18px;\n"
"  height: 18px;\n"
"\n"
"  /* Rounded corners for the indicator box */\n"
"  border-radius: 4px;\n"
"\n"
"  /* Defau"
                        "lt (Unchecked) State */\n"
"  border: 2px solid #7f8c8d;\n"
"  /* Muted gray border */\n"
"  background-color: #34495e;\n"
"  /* Darker fill for the box */\n"
"}\n"
"\n"
"/* ----------------------------------------------------\n"
"   QCheckBox CHECKED STATE\n"
"   ---------------------------------------------------- */\n"
"\n"
"QCheckBox::indicator:checked {\n"
"  /* When checked, change the background and border to the accent color */\n"
"  border: 2px solid #3498db;\n"
"  /* Primary Blue Border */\n"
"  background-color: #3498db;\n"
"  /* Primary Blue Fill */\n"
"\n"
"  /* Set the icon/check mark inside the box */\n"
"  image: url(:/icons/check.png);\n"
"  /* Assumes you have a white checkmark SVG/PNG in your QRC */\n"
"}\n"
"\n"
"\n"
"/* ----------------------------------------------------\n"
"   QCheckBox INTERACTIVE STATES\n"
"   ---------------------------------------------------- */\n"
"\n"
"QCheckBox::indicator:hover {\n"
"  /* Subtle change when hovering over the indicator */\n"
"  border-color: #95a5"
                        "a6;\n"
"  /* Lighten border slightly */\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover {\n"
"  /* Slightly darker blue on checked hover */\n"
"  background-color: #2980b9;\n"
"  border-color: #2980b9;\n"
"}\n"
"\n"
"QCheckBox::indicator:disabled {\n"
"  /* Mute the colors when the checkbox is disabled */\n"
"  background-color: #7f8c8d;\n"
"  border-color: #7f8c8d;\n"
"}")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.card = QFrame(self.centralwidget)
        self.card.setObjectName(u"card")
        self.card.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.card.sizePolicy().hasHeightForWidth())
        self.card.setSizePolicy(sizePolicy)
        self.card.setMinimumSize(QSize(900, 640))
        self.card.setFrameShape(QFrame.Shape.NoFrame)
        self.card.setFrameShadow(QFrame.Shadow.Raised)
        self.cardLayout = QVBoxLayout(self.card)
        self.cardLayout.setObjectName(u"cardLayout")
        self.topBarLayout = QHBoxLayout()
        self.topBarLayout.setObjectName(u"topBarLayout")
        self.brandingLayout = QHBoxLayout()
        self.brandingLayout.setObjectName(u"brandingLayout")
        self.titleLayout = QVBoxLayout()
        self.titleLayout.setObjectName(u"titleLayout")
        self.logoLabel = QLabel(self.card)
        self.logoLabel.setObjectName(u"logoLabel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy1)
        self.logoLabel.setMinimumSize(QSize(292, 83))
        self.logoLabel.setStyleSheet(u"QLabel { font-size: 20px; border-radius: 10px; padding: 8px; }")
        self.logoLabel.setPixmap(QPixmap(u":/icons/logo_biale.svg"))
        self.logoLabel.setScaledContents(True)
        self.logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.titleLayout.addWidget(self.logoLabel)


        self.brandingLayout.addLayout(self.titleLayout)


        self.topBarLayout.addLayout(self.brandingLayout)

        self.hSpacer1 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.topBarLayout.addItem(self.hSpacer1)

        self.loginLayout = QHBoxLayout()
        self.loginLayout.setSpacing(9)
        self.loginLayout.setObjectName(u"loginLayout")
        self.logout_bnt = QPushButton(self.card)
        self.logout_bnt.setObjectName(u"logout_bnt")
        font = QFont()
        font.setPointSize(10)
        self.logout_bnt.setFont(font)
        icon = QIcon()
        icon.addFile(u":/icons/log-in.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.logout_bnt.setIcon(icon)
        self.logout_bnt.setIconSize(QSize(40, 40))

        self.loginLayout.addWidget(self.logout_bnt)

        self.emailInput = QLineEdit(self.card)
        self.emailInput.setObjectName(u"emailInput")
        font1 = QFont()
        font1.setPointSize(11)
        self.emailInput.setFont(font1)

        self.loginLayout.addWidget(self.emailInput)

        self.passwordInput = QLineEdit(self.card)
        self.passwordInput.setObjectName(u"passwordInput")
        self.passwordInput.setFont(font1)
        self.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)

        self.loginLayout.addWidget(self.passwordInput)

        self.logInBnt = QPushButton(self.card)
        self.logInBnt.setObjectName(u"logInBnt")
        font2 = QFont()
        font2.setPointSize(11)
        font2.setWeight(QFont.DemiBold)
        self.logInBnt.setFont(font2)

        self.loginLayout.addWidget(self.logInBnt)

        self.language_icon = QLabel(self.card)
        self.language_icon.setObjectName(u"language_icon")
        font3 = QFont()
        font3.setPointSize(8)
        self.language_icon.setFont(font3)
        self.language_icon.setPixmap(QPixmap(u":/icons/languages.png"))

        self.loginLayout.addWidget(self.language_icon)

        self.langCombo = QComboBox(self.card)
        self.langCombo.addItem("")
        self.langCombo.addItem("")
        self.langCombo.addItem("")
        self.langCombo.setObjectName(u"langCombo")
        self.langCombo.setFont(font1)

        self.loginLayout.addWidget(self.langCombo)


        self.topBarLayout.addLayout(self.loginLayout)


        self.cardLayout.addLayout(self.topBarLayout)

        self.controlsFrame = QFrame(self.card)
        self.controlsFrame.setObjectName(u"controlsFrame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.controlsFrame.sizePolicy().hasHeightForWidth())
        self.controlsFrame.setSizePolicy(sizePolicy2)
        self.controlsFrame.setMinimumSize(QSize(0, 70))
        self.controlsFrame.setMaximumSize(QSize(16777215, 100))
        self.controlsFrame.setBaseSize(QSize(0, 0))
        self.controlsFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.controlsLayout = QHBoxLayout(self.controlsFrame)
        self.controlsLayout.setSpacing(9)
        self.controlsLayout.setObjectName(u"controlsLayout")
        self.controlsLayout.setContentsMargins(3, -1, 3, -1)
        self.randomAnimButton = QPushButton(self.controlsFrame)
        self.randomAnimButton.setObjectName(u"randomAnimButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.randomAnimButton.sizePolicy().hasHeightForWidth())
        self.randomAnimButton.setSizePolicy(sizePolicy3)
        self.randomAnimButton.setFont(font2)
        icon1 = QIcon()
        icon1.addFile(u":/icons/shuffle_blue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.randomAnimButton.setIcon(icon1)
        self.randomAnimButton.setIconSize(QSize(20, 20))

        self.controlsLayout.addWidget(self.randomAnimButton)

        self.randomButton = QPushButton(self.controlsFrame)
        self.randomButton.setObjectName(u"randomButton")
        sizePolicy3.setHeightForWidth(self.randomButton.sizePolicy().hasHeightForWidth())
        self.randomButton.setSizePolicy(sizePolicy3)
        self.randomButton.setFont(font2)
        self.randomButton.setIcon(icon1)
        self.randomButton.setIconSize(QSize(20, 20))

        self.controlsLayout.addWidget(self.randomButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.controlsLayout.addItem(self.horizontalSpacer)

        self.browseButton = QPushButton(self.controlsFrame)
        self.browseButton.setObjectName(u"browseButton")
        self.browseButton.setFont(font2)
        self.browseButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon2 = QIcon()
        icon2.addFile(u":/icons/images_blue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.browseButton.setIcon(icon2)
        self.browseButton.setIconSize(QSize(20, 20))

        self.controlsLayout.addWidget(self.browseButton)


        self.cardLayout.addWidget(self.controlsFrame)

        self.add_file_h_layout = QHBoxLayout()
        self.add_file_h_layout.setObjectName(u"add_file_h_layout")
        self.add_files_icon = QLabel(self.card)
        self.add_files_icon.setObjectName(u"add_files_icon")
        self.add_files_icon.setPixmap(QPixmap(u":/icons/upload.png"))

        self.add_file_h_layout.addWidget(self.add_files_icon)

        self.add_file_label = QLabel(self.card)
        self.add_file_label.setObjectName(u"add_file_label")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.add_file_label.sizePolicy().hasHeightForWidth())
        self.add_file_label.setSizePolicy(sizePolicy4)
        font4 = QFont()
        font4.setPointSize(14)
        font4.setBold(True)
        self.add_file_label.setFont(font4)

        self.add_file_h_layout.addWidget(self.add_file_label)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.add_file_h_layout.addItem(self.horizontalSpacer_6)


        self.cardLayout.addLayout(self.add_file_h_layout)

        self.uploadArea = QFrame(self.card)
        self.uploadArea.setObjectName(u"uploadArea")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.uploadArea.sizePolicy().hasHeightForWidth())
        self.uploadArea.setSizePolicy(sizePolicy5)
        self.uploadArea.setMinimumSize(QSize(0, 160))
        self.uploadArea.setAcceptDrops(True)
        self.uploadArea.setAutoFillBackground(False)
        self.uploadArea.setStyleSheet(u"")
        self.uploadLayout = QVBoxLayout(self.uploadArea)
        self.uploadLayout.setSpacing(14)
        self.uploadLayout.setObjectName(u"uploadLayout")
        self.uploadLayout.setContentsMargins(-1, 9, -1, -1)
        self.upload_area_empty_frame = QFrame(self.uploadArea)
        self.upload_area_empty_frame.setObjectName(u"upload_area_empty_frame")
        self.upload_area_empty_v_box = QVBoxLayout(self.upload_area_empty_frame)
        self.upload_area_empty_v_box.setObjectName(u"upload_area_empty_v_box")
        self.uploadIcon = QLabel(self.upload_area_empty_frame)
        self.uploadIcon.setObjectName(u"uploadIcon")
        self.uploadIcon.setAutoFillBackground(False)
        self.uploadIcon.setStyleSheet(u"")
        self.uploadIcon.setPixmap(QPixmap(u":/icons/upload.png"))
        self.uploadIcon.setScaledContents(False)
        self.uploadIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.upload_area_empty_v_box.addWidget(self.uploadIcon)

        self.uploadText = QLabel(self.upload_area_empty_frame)
        self.uploadText.setObjectName(u"uploadText")
        sizePolicy3.setHeightForWidth(self.uploadText.sizePolicy().hasHeightForWidth())
        self.uploadText.setSizePolicy(sizePolicy3)
        self.uploadText.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.upload_area_empty_v_box.addWidget(self.uploadText)

        self.uploadSupported = QLabel(self.upload_area_empty_frame)
        self.uploadSupported.setObjectName(u"uploadSupported")
        self.uploadSupported.setStyleSheet(u"QLabel { color: rgba(255,255,255,0.72); font-size:11px; }")
        self.uploadSupported.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uploadSupported.setMargin(0)

        self.upload_area_empty_v_box.addWidget(self.uploadSupported)


        self.uploadLayout.addWidget(self.upload_area_empty_frame)


        self.cardLayout.addWidget(self.uploadArea)

        self.url_loader_qframe = QFrame(self.card)
        self.url_loader_qframe.setObjectName(u"url_loader_qframe")
        sizePolicy4.setHeightForWidth(self.url_loader_qframe.sizePolicy().hasHeightForWidth())
        self.url_loader_qframe.setSizePolicy(sizePolicy4)
        self.url_loader_qframe.setMinimumSize(QSize(0, 0))
        self.url_loader_qframe.setFrameShape(QFrame.Shape.NoFrame)
        self.url_loader_qframe.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout_2 = QVBoxLayout(self.url_loader_qframe)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(3, -1, 3, -1)
        self.url_loader_lable_Hbox = QHBoxLayout()
        self.url_loader_lable_Hbox.setSpacing(6)
        self.url_loader_lable_Hbox.setObjectName(u"url_loader_lable_Hbox")
        self.url_loader_lable_Hbox.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.icon_label = QLabel(self.url_loader_qframe)
        self.icon_label.setObjectName(u"icon_label")
        sizePolicy2.setHeightForWidth(self.icon_label.sizePolicy().hasHeightForWidth())
        self.icon_label.setSizePolicy(sizePolicy2)
        self.icon_label.setPixmap(QPixmap(u":/icons/link.png"))

        self.url_loader_lable_Hbox.addWidget(self.icon_label)

        self.url_loader_text_label = QLabel(self.url_loader_qframe)
        self.url_loader_text_label.setObjectName(u"url_loader_text_label")
        self.url_loader_text_label.setEnabled(True)
        sizePolicy4.setHeightForWidth(self.url_loader_text_label.sizePolicy().hasHeightForWidth())
        self.url_loader_text_label.setSizePolicy(sizePolicy4)
        font5 = QFont()
        font5.setPointSize(15)
        font5.setBold(True)
        self.url_loader_text_label.setFont(font5)

        self.url_loader_lable_Hbox.addWidget(self.url_loader_text_label)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.url_loader_lable_Hbox.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addLayout(self.url_loader_lable_Hbox)

        self.urlLayout = QHBoxLayout()
        self.urlLayout.setSpacing(9)
        self.urlLayout.setObjectName(u"urlLayout")
        self.urlLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.urlInput = QLineEdit(self.url_loader_qframe)
        self.urlInput.setObjectName(u"urlInput")
        self.urlInput.setMinimumSize(QSize(0, 38))
        font6 = QFont()
        font6.setPointSize(12)
        self.urlInput.setFont(font6)

        self.urlLayout.addWidget(self.urlInput)

        self.loadUrlButton = QPushButton(self.url_loader_qframe)
        self.loadUrlButton.setObjectName(u"loadUrlButton")
        sizePolicy3.setHeightForWidth(self.loadUrlButton.sizePolicy().hasHeightForWidth())
        self.loadUrlButton.setSizePolicy(sizePolicy3)
        self.loadUrlButton.setMinimumSize(QSize(92, 42))
        font7 = QFont()
        font7.setPointSize(12)
        font7.setWeight(QFont.DemiBold)
        self.loadUrlButton.setFont(font7)
        self.loadUrlButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.urlLayout.addWidget(self.loadUrlButton)


        self.verticalLayout_2.addLayout(self.urlLayout)

        self.url_helper_text_label = QLabel(self.url_loader_qframe)
        self.url_helper_text_label.setObjectName(u"url_helper_text_label")
        sizePolicy2.setHeightForWidth(self.url_helper_text_label.sizePolicy().hasHeightForWidth())
        self.url_helper_text_label.setSizePolicy(sizePolicy2)
        self.url_helper_text_label.setBaseSize(QSize(0, 0))
        font8 = QFont()
        font8.setPointSize(7)
        font8.setItalic(True)
        font8.setStrikeOut(False)
        font8.setKerning(True)
        self.url_helper_text_label.setFont(font8)

        self.verticalLayout_2.addWidget(self.url_helper_text_label)


        self.cardLayout.addWidget(self.url_loader_qframe)

        self.autoFrame = QFrame(self.card)
        self.autoFrame.setObjectName(u"autoFrame")
        sizePolicy2.setHeightForWidth(self.autoFrame.sizePolicy().hasHeightForWidth())
        self.autoFrame.setSizePolicy(sizePolicy2)
        self.autoFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.autoLayout = QVBoxLayout(self.autoFrame)
        self.autoLayout.setSpacing(0)
        self.autoLayout.setObjectName(u"autoLayout")
        self.autoLayout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.autoLayout.setContentsMargins(3, 6, 3, 0)
        self.autoTopLayout = QHBoxLayout()
        self.autoTopLayout.setSpacing(0)
        self.autoTopLayout.setObjectName(u"autoTopLayout")
        self.autoTopLayout.setContentsMargins(-1, -1, -1, 5)
        self.auto_change_icon_lable = QLabel(self.autoFrame)
        self.auto_change_icon_lable.setObjectName(u"auto_change_icon_lable")
        font9 = QFont()
        font9.setBold(False)
        self.auto_change_icon_lable.setFont(font9)
        self.auto_change_icon_lable.setPixmap(QPixmap(u":/icons/timer.png"))
        self.auto_change_icon_lable.setScaledContents(False)

        self.autoTopLayout.addWidget(self.auto_change_icon_lable)

        self.autoLabel = QLabel(self.autoFrame)
        self.autoLabel.setObjectName(u"autoLabel")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.autoLabel.sizePolicy().hasHeightForWidth())
        self.autoLabel.setSizePolicy(sizePolicy6)
        self.autoLabel.setFont(font5)

        self.autoTopLayout.addWidget(self.autoLabel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.autoTopLayout.addItem(self.horizontalSpacer_2)

        self.enabledCheck = QCheckBox(self.autoFrame)
        self.enabledCheck.setObjectName(u"enabledCheck")
        font10 = QFont()
        font10.setPointSize(13)
        self.enabledCheck.setFont(font10)
        self.enabledCheck.setChecked(True)

        self.autoTopLayout.addWidget(self.enabledCheck)


        self.autoLayout.addLayout(self.autoTopLayout)


        self.cardLayout.addWidget(self.autoFrame)

        self.source_n_interval_frame = QFrame(self.card)
        self.source_n_interval_frame.setObjectName(u"source_n_interval_frame")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.source_n_interval_frame.sizePolicy().hasHeightForWidth())
        self.source_n_interval_frame.setSizePolicy(sizePolicy7)
        self.source_n_interval_frame.setMinimumSize(QSize(0, 80))
        font11 = QFont()
        font11.setKerning(True)
        self.source_n_interval_frame.setFont(font11)
        self.source_n_interval_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.source_n_interval_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.source_n_interval_frame)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(3, 6, 3, 3)
        self.interval_v_layout = QVBoxLayout()
        self.interval_v_layout.setSpacing(3)
        self.interval_v_layout.setObjectName(u"interval_v_layout")
        self.interval_v_layout.setContentsMargins(-1, -1, -1, 0)
        self.inverval_lable = QLabel(self.source_n_interval_frame)
        self.inverval_lable.setObjectName(u"inverval_lable")
        font12 = QFont()
        font12.setPointSize(13)
        font12.setBold(True)
        self.inverval_lable.setFont(font12)

        self.interval_v_layout.addWidget(self.inverval_lable)

        self.interval_spinBox = QSpinBox(self.source_n_interval_frame)
        self.interval_spinBox.setObjectName(u"interval_spinBox")
        self.interval_spinBox.setMinimumSize(QSize(0, 35))
        self.interval_spinBox.setFont(font1)
        self.interval_spinBox.setWrapping(False)
        self.interval_spinBox.setFrame(False)
        self.interval_spinBox.setMaximum(999999)
        self.interval_spinBox.setSingleStep(5)

        self.interval_v_layout.addWidget(self.interval_spinBox)


        self.horizontalLayout_5.addLayout(self.interval_v_layout)

        self.source_v_layout = QVBoxLayout()
        self.source_v_layout.setSpacing(9)
        self.source_v_layout.setObjectName(u"source_v_layout")
        self.source_v_layout.setContentsMargins(-1, -1, -1, 0)
        self.wallpaper_source_lable = QLabel(self.source_n_interval_frame)
        self.wallpaper_source_lable.setObjectName(u"wallpaper_source_lable")
        self.wallpaper_source_lable.setFont(font12)

        self.source_v_layout.addWidget(self.wallpaper_source_lable)

        self.source_inner_h_loyout = QHBoxLayout()
        self.source_inner_h_loyout.setObjectName(u"source_inner_h_loyout")
        self.super_wallpaper_btn = QPushButton(self.source_n_interval_frame)
        self.super_wallpaper_btn.setObjectName(u"super_wallpaper_btn")
        self.super_wallpaper_btn.setFont(font2)
        self.super_wallpaper_btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        icon3 = QIcon()
        icon3.addFile(u":/icons/sparkles_blue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.super_wallpaper_btn.setIcon(icon3)

        self.source_inner_h_loyout.addWidget(self.super_wallpaper_btn)

        self.fvrt_wallpapers_btn = QPushButton(self.source_n_interval_frame)
        self.fvrt_wallpapers_btn.setObjectName(u"fvrt_wallpapers_btn")
        self.fvrt_wallpapers_btn.setFont(font1)
        icon4 = QIcon()
        icon4.addFile(u":/icons/heart.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.fvrt_wallpapers_btn.setIcon(icon4)

        self.source_inner_h_loyout.addWidget(self.fvrt_wallpapers_btn)

        self.added_wallpaper_btn = QPushButton(self.source_n_interval_frame)
        self.added_wallpaper_btn.setObjectName(u"added_wallpaper_btn")
        self.added_wallpaper_btn.setFont(font1)
        icon5 = QIcon()
        icon5.addFile(u":/icons/circle-plus.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.added_wallpaper_btn.setIcon(icon5)

        self.source_inner_h_loyout.addWidget(self.added_wallpaper_btn)


        self.source_v_layout.addLayout(self.source_inner_h_loyout)


        self.horizontalLayout_5.addLayout(self.source_v_layout)


        self.cardLayout.addWidget(self.source_n_interval_frame)

        self.range_frame = QFrame(self.card)
        self.range_frame.setObjectName(u"range_frame")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.range_frame.sizePolicy().hasHeightForWidth())
        self.range_frame.setSizePolicy(sizePolicy8)
        self.range_frame.setMinimumSize(QSize(0, 100))
        self.range_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.range_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.range_frame)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(3, 0, 3, -1)
        self.range_v_layout = QVBoxLayout()
        self.range_v_layout.setSpacing(0)
        self.range_v_layout.setObjectName(u"range_v_layout")
        self.range_lable = QLabel(self.range_frame)
        self.range_lable.setObjectName(u"range_lable")
        self.range_lable.setMinimumSize(QSize(0, 0))
        self.range_lable.setFont(font12)
        self.range_lable.setStyleSheet(u"")

        self.range_v_layout.addWidget(self.range_lable)

        self.range_inner_h_layout = QHBoxLayout()
        self.range_inner_h_layout.setSpacing(6)
        self.range_inner_h_layout.setObjectName(u"range_inner_h_layout")
        self.range_all_bnt = QPushButton(self.range_frame)
        self.range_all_bnt.setObjectName(u"range_all_bnt")
        self.range_all_bnt.setFont(font2)
        icon6 = QIcon()
        icon6.addFile(u":/icons/wallpaper_blue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.range_all_bnt.setIcon(icon6)
        self.range_all_bnt.setIconSize(QSize(20, 20))

        self.range_inner_h_layout.addWidget(self.range_all_bnt)

        self.range_wallpaper_bnt = QPushButton(self.range_frame)
        self.range_wallpaper_bnt.setObjectName(u"range_wallpaper_bnt")
        self.range_wallpaper_bnt.setFont(font1)
        icon7 = QIcon()
        icon7.addFile(u":/icons/film.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.range_wallpaper_bnt.setIcon(icon7)
        self.range_wallpaper_bnt.setIconSize(QSize(20, 20))

        self.range_inner_h_layout.addWidget(self.range_wallpaper_bnt)

        self.range_mp4_bnt = QPushButton(self.range_frame)
        self.range_mp4_bnt.setObjectName(u"range_mp4_bnt")
        self.range_mp4_bnt.setFont(font1)
        self.range_mp4_bnt.setIcon(icon7)
        self.range_mp4_bnt.setIconSize(QSize(20, 20))

        self.range_inner_h_layout.addWidget(self.range_mp4_bnt)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.range_inner_h_layout.addItem(self.horizontalSpacer_5)


        self.range_v_layout.addLayout(self.range_inner_h_layout)


        self.horizontalLayout_6.addLayout(self.range_v_layout)


        self.cardLayout.addWidget(self.range_frame)

        self.bottomFrame = QFrame(self.card)
        self.bottomFrame.setObjectName(u"bottomFrame")
        self.bottomLayout = QHBoxLayout(self.bottomFrame)
        self.bottomLayout.setObjectName(u"bottomLayout")
        self.statusLabel = QLabel(self.bottomFrame)
        self.statusLabel.setObjectName(u"statusLabel")
        font13 = QFont()
        font13.setPointSize(9)
        font13.setBold(True)
        self.statusLabel.setFont(font13)

        self.bottomLayout.addWidget(self.statusLabel)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottomLayout.addItem(self.horizontalSpacer_3)


        self.cardLayout.addWidget(self.bottomFrame)


        self.verticalLayout.addWidget(self.card)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.urlInput.returnPressed.connect(self.loadUrlButton.click)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Tapeciarnia", None))
        self.logoLabel.setText("")
        self.logoLabel.setProperty(u"icon", QCoreApplication.translate("MainWindow", u"\";/icons/llogo_biale.svg\"", None))
#if QT_CONFIG(tooltip)
        self.logout_bnt.setToolTip(QCoreApplication.translate("MainWindow", u"log out", None))
#endif // QT_CONFIG(tooltip)
        self.logout_bnt.setText("")
        self.emailInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"email", None))
        self.passwordInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"password", None))
#if QT_CONFIG(tooltip)
        self.logInBnt.setToolTip(QCoreApplication.translate("MainWindow", u"Sign in", None))
#endif // QT_CONFIG(tooltip)
        self.logInBnt.setText(QCoreApplication.translate("MainWindow", u"Log In", None))
        self.logInBnt.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.language_icon.setText("")
        self.langCombo.setItemText(0, QCoreApplication.translate("MainWindow", u"EN", None))
        self.langCombo.setItemText(1, QCoreApplication.translate("MainWindow", u"PL", None))
        self.langCombo.setItemText(2, QCoreApplication.translate("MainWindow", u"DE", None))

        self.randomAnimButton.setText(QCoreApplication.translate("MainWindow", u"  Shuffle animated", None))
        self.randomAnimButton.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.randomButton.setText(QCoreApplication.translate("MainWindow", u"  Shuffle wallpaper", None))
        self.randomButton.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.browseButton.setText(QCoreApplication.translate("MainWindow", u"  Browse wallpapers", None))
        self.browseButton.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.add_files_icon.setText("")
        self.add_file_label.setText(QCoreApplication.translate("MainWindow", u"Add files", None))
        self.uploadIcon.setText("")
        self.uploadText.setText(QCoreApplication.translate("MainWindow", u"Drag & drop a photo or video here, or click to choose a file", None))
        self.uploadSupported.setText(QCoreApplication.translate("MainWindow", u"Supported: JPG, PNG, MP4", None))
        self.icon_label.setText("")
        self.url_loader_text_label.setText(QCoreApplication.translate("MainWindow", u"Images or Video URL", None))
        self.urlInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"https://example.com/image.jpg or https://.../video.mp4", None))
        self.loadUrlButton.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.loadUrlButton.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.url_helper_text_label.setText(QCoreApplication.translate("MainWindow", u"Paete a dirick link to a .jpg/.png or mp4", None))
        self.auto_change_icon_lable.setText("")
        self.autoLabel.setText(QCoreApplication.translate("MainWindow", u"Automatic wallpaper change", None))
        self.enabledCheck.setText(QCoreApplication.translate("MainWindow", u"Enabled", None))
        self.inverval_lable.setText(QCoreApplication.translate("MainWindow", u"Interval (minutes)", None))
        self.wallpaper_source_lable.setText(QCoreApplication.translate("MainWindow", u"Wallpaper source", None))
        self.super_wallpaper_btn.setText(QCoreApplication.translate("MainWindow", u"  Super Wallpaper", None))
        self.super_wallpaper_btn.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.fvrt_wallpapers_btn.setText(QCoreApplication.translate("MainWindow", u"  Favorite Wallpapers", None))
        self.fvrt_wallpapers_btn.setProperty(u"class", QCoreApplication.translate("MainWindow", u"ghost", None))
        self.added_wallpaper_btn.setText(QCoreApplication.translate("MainWindow", u"  Added wallpapers", None))
        self.added_wallpaper_btn.setProperty(u"class", QCoreApplication.translate("MainWindow", u"ghost", None))
        self.range_lable.setText(QCoreApplication.translate("MainWindow", u"Range", None))
        self.range_all_bnt.setText(QCoreApplication.translate("MainWindow", u"  All", None))
        self.range_all_bnt.setProperty(u"class", QCoreApplication.translate("MainWindow", u"primary", None))
        self.range_wallpaper_bnt.setText(QCoreApplication.translate("MainWindow", u"  Wallpaper", None))
        self.range_wallpaper_bnt.setProperty(u"class", QCoreApplication.translate("MainWindow", u"ghost", None))
        self.range_mp4_bnt.setText(QCoreApplication.translate("MainWindow", u"  Mp4", None))
        self.range_mp4_bnt.setProperty(u"class", QCoreApplication.translate("MainWindow", u"ghost", None))
        self.statusLabel.setText(QCoreApplication.translate("MainWindow", u"Status: min ,Status: min ,Status: min ,Status: min", None))
    # retranslateUi

