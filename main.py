import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, 
    QProgressBar, QHBoxLayout, QTimeEdit, QSystemTrayIcon, QMenu, QAction,
    QDesktopWidget, QGraphicsOpacityEffect, QGraphicsBlurEffect, QFrame,
    QMessageBox
)
from PyQt5.QtGui import QIcon, QFontDatabase, QColor, QPainter, QLinearGradient, QFont, QPainterPath
from PyQt5.QtCore import QTimer, QTime, QDateTime, Qt, QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup, QRectF
from PyQt5.QtMultimedia import QSound
from datetime import datetime, timedelta
import screeninfo
import tempfile

class WaterReminder(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.alert_widget = None
        self.interval = 60  # Default interval of 60 minutes
        self.hydration_started = False
        self.lock_file = os.path.join(tempfile.gettempdir(), 'water_reminder.lock')

    def initUI(self):
        self.setWindowTitle("Kawaii Water Buddy")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Comfortaa', sans-serif;
                color: #000000;
                background-color: transparent;
            }
            QLabel {
                font-size: 18px;
            }
            QLineEdit, QTimeEdit {
                font-size: 16px;
                padding: 8px;
                border-radius: 15px;
                border: 2px solid #000000;
                background-color: rgba(255, 255, 255, 0.7);
                color: #000000;
            }
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 20px;
                background-color: rgba(255, 255, 255, 0.7);
                color: #000000;
                border: 2px solid #000000;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9);
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.7);
            }
            QProgressBar::chunk {
                background-color: #FF69B4;
                border-radius: 10px;
            }
            QTimeEdit::up-button, QTimeEdit::down-button {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.7);
            }
            QTimeEdit::up-arrow, QTimeEdit::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)

        main_layout = QVBoxLayout()

        # Add top buttons for close and minimize
        top_buttons_layout = QHBoxLayout()
        close_button = QPushButton("×")
        minimize_button = QPushButton("−")
        close_button.setFixedSize(30, 30)
        minimize_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        minimize_button.clicked.connect(self.showMinimized)
        top_buttons_layout.addWidget(minimize_button)
        top_buttons_layout.addWidget(close_button)
        top_buttons_layout.setAlignment(Qt.AlignRight)
        main_layout.addLayout(top_buttons_layout)

        # Create a frame for the content
        content_frame = QFrame(self)
        content_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 20px;
                padding: 20px;
            }
        """)
        content_layout = QVBoxLayout(content_frame)

        # Cute title
        title_label = QLabel("Stay Hydrated, Senpai! ✧◝(⁰▿⁰)◜✧")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #000000;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        # Input fields
        input_layout = QHBoxLayout()
        
        left_panel = QVBoxLayout()
        self.interval_label = QLabel("Hydration interval (mins):")
        self.interval_input = QLineEdit("60")
        left_panel.addWidget(self.interval_label)
        left_panel.addWidget(self.interval_input)
        
        self.goal_label = QLabel("Daily hydration goal:")
        self.goal_input = QLineEdit("8")
        left_panel.addWidget(self.goal_label)
        left_panel.addWidget(self.goal_input)
        
        input_layout.addLayout(left_panel)
        
        right_panel = QVBoxLayout()
        self.work_hours_label = QLabel("Hydration hours:")
        time_layout = QHBoxLayout()
        self.start_time_input = QTimeEdit(QTime(9, 0))
        self.end_time_input = QTimeEdit(QTime(17, 0))
        time_layout.addWidget(self.start_time_input)
        time_layout.addWidget(self.end_time_input)
        right_panel.addWidget(self.work_hours_label)
        right_panel.addLayout(time_layout)
        
        input_layout.addLayout(right_panel)
        
        content_layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Hydration Journey!")
        self.start_button.clicked.connect(self.start_reminder)
        self.drink_now_button = QPushButton("I Drank! (◕‿◕✿)")
        self.drink_now_button.clicked.connect(self.drink_water)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.drink_now_button)
        content_layout.addLayout(button_layout)

        # Progress and countdown
        self.progress_label = QLabel("Hydration Progress: 0/0")
        self.progress_bar = QProgressBar()
        self.countdown_label = QLabel("Next hydration in: 00:00")
        self.countdown_bar = QProgressBar()
        self.countdown_bar.setRange(0, 100)
        
        content_layout.addWidget(self.progress_label)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.countdown_label)
        content_layout.addWidget(self.countdown_bar)

        self.time_label = QLabel("")
        self.update_time()
        content_layout.addWidget(self.time_label)

        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)

        self.drinks_taken = 0
        self.goal = 8

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.setWindowIcon(QIcon("icon.png"))

        # System tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        tray_menu = QMenu()
        show_action = QAction("Show Hydration Buddy", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Sayonara!", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

        # Window effects
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Animation effects
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)

        self.expand_animation = QPropertyAnimation(self, b"geometry")
        self.expand_animation.setDuration(1000)
        self.expand_animation.setStartValue(QRect(100, 100, 0, 0))
        self.expand_animation.setEndValue(QRect(100, 100, 600, 400))
        self.expand_animation.setEasingCurve(QEasingCurve.OutElastic)

        # Combine animations
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.fade_animation)
        self.animation_group.addAnimation(self.expand_animation)

    def showEvent(self, event):
        super().showEvent(event)
        self.animation_group.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 30, 30)

        # Set the clip path
        painter.setClipPath(path)

        # Draw the gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(255, 182, 193, 220))  # Light pink
        gradient.setColorAt(1, QColor(173, 216, 230, 220))  # Light blue
        painter.fillPath(path, gradient)

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"Current Time: {now}")
        QTimer.singleShot(1000, self.update_time)

    def start_reminder(self):
        self.interval = int(self.interval_input.text())
        self.start_time = self.start_time_input.time().toPyTime()
        self.end_time = self.end_time_input.time().toPyTime()
        self.goal = int(self.goal_input.text())
        self.progress_bar.setMaximum(self.goal)
        self.hydration_started = True

        self.update_progress_label()

        self.next_drink_time = datetime.now() + timedelta(minutes=self.interval)
        self.timer.start(1000)

        # Add a little animation when starting
        self.start_button.setEnabled(False)
        self.start_animation = QPropertyAnimation(self.start_button, b"geometry")
        self.start_animation.setDuration(300)
        self.start_animation.setKeyValueAt(0, self.start_button.geometry())
        self.start_animation.setKeyValueAt(0.5, self.start_button.geometry().adjusted(-5, -5, 5, 5))
        self.start_animation.setKeyValueAt(1, self.start_button.geometry())
        self.start_animation.start()
        QTimer.singleShot(300, lambda: self.start_button.setEnabled(True))

    def update_timer(self):
        current_time = datetime.now()
        if self.start_time <= current_time.time() <= self.end_time:
            if current_time >= self.next_drink_time:
                self.show_full_screen_alert()
            else:
                time_left = self.next_drink_time - current_time
                total_seconds = time_left.total_seconds()
                mins, secs = divmod(int(total_seconds), 60)
                time_format = f"{mins:02d}:{secs:02d}"
                self.countdown_label.setText(f"Next hydration in: {time_format}")
                
                progress = 100 - (total_seconds / (self.interval * 60) * 100)
                self.countdown_bar.setValue(int(progress))
                
                self.update_progress_label()
        else:
            self.countdown_label.setText("Hydration time is over! (´｡• ω •｡`)")
            self.countdown_bar.setValue(0)
            self.update_progress_label()

    def drink_water(self):
        self.drinks_taken += 1
        self.progress_bar.setValue(self.drinks_taken)
        self.update_progress_label()
        self.next_drink_time = datetime.now() + timedelta(minutes=self.interval)
        if self.alert_widget:
            self.alert_widget.close()
            self.alert_widget = None

        # Add a little animation when drinking
        self.drink_animation = QPropertyAnimation(self.drink_now_button, b"geometry")
        self.drink_animation.setDuration(300)
        self.drink_animation.setKeyValueAt(0, self.drink_now_button.geometry())
        self.drink_animation.setKeyValueAt(0.5, self.drink_now_button.geometry().adjusted(-5, -5, 5, 5))
        self.drink_animation.setKeyValueAt(1, self.drink_now_button.geometry())
        self.drink_animation.start()

    def update_progress_label(self):
        self.progress_label.setText(f"Hydration Progress: {self.drinks_taken}/{self.goal}")

    def show_full_screen_alert(self):
        if not self.alert_widget:
            self.alert_widget = QWidget()
            self.alert_widget.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.alert_widget.setAttribute(Qt.WA_TranslucentBackground)
            self.alert_widget.setStyleSheet("background-color: rgba(255, 182, 193, 220); border-radius: 30px;")
            
            label = QLabel("Time to hydrate, Senpai! (づ｡◕‿‿◕｡)づ", self.alert_widget)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #000000; font-size: 36px; font-weight: bold;")
            
            drink_button = QPushButton("I'm Hydrated! ヽ(^o^)ノ", self.alert_widget)
            drink_button.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    padding: 15px;
                    border-radius: 25px;
                    background-color: rgba(255, 255, 255, 0.7);
                    color: #000000;
                    border: 2px solid #000000;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.9);
                }
            """)
            drink_button.clicked.connect(self.drink_water)
            
            layout = QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(drink_button)
            self.alert_widget.setLayout(layout)
            
            screen = QDesktopWidget().screenNumber(QDesktopWidget().cursor().pos())
            screen_geometry = QDesktopWidget().screenGeometry(screen)
            self.alert_widget.setGeometry(screen_geometry)
            
            self.alert_widget.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def closeEvent(self, event):
        if not self.hydration_started:
            self.quit_app()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("Water Reminder", "The app is still running in the background.", QSystemTrayIcon.Information, 3000)

    def quit_app(self):
        self.tray_icon.hide()
        os.remove(self.lock_file)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    QFontDatabase.addApplicationFont("./Comfortaa-Regular.ttf")

    # Check if the program is already running
    if os.path.exists(os.path.join(tempfile.gettempdir(), 'water_reminder.lock')):
        QMessageBox.warning(None, "Water Reminder", "The program is already running!")
        sys.exit()

    # Create a lock file
    with open(os.path.join(tempfile.gettempdir(), 'water_reminder.lock'), 'w') as f:
        f.write(str(os.getpid()))

    water_reminder = WaterReminder()
    water_reminder.show()

    sys.exit(app.exec_())
