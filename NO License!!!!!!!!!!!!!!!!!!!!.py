import os
import ctypes
import winreg
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

# --- Windows 設定操作（ダーク/ライト切替・壁紙変更） ---
def set_dark_mode(dark=True):
    """
    Windows のダーク/ライト（AppsUseLightTheme, SystemUsesLightTheme）を切り替えます。
    注意: レジストリ操作には適切な権限が必要です。
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            val = 0 if dark else 1
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, val)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, val)
        return True, f"{'ダークモード' if dark else 'ライトモード'} へ変更しました\n完全に適応するには再起動してください"
    except PermissionError:
        return False, "権限不足のため書き込みができませんでした"
    except Exception as e:
        return False, f"Erro: {e}"

def set_wallpaper(path):
    if not path:
        return False, "壁紙のパスが空です"
    abs_path = os.path.abspath(path)
    try:
        key_path = r"Control Panel\Desktop"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, abs_path)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
        return True, "壁紙を変更しました"
    except PermissionError:
        return False, "権限不足のため書き込みができませんでした"
    except Exception as e:
        return False, f"エラーが発生しました: {e}"

# --- GUI ---
class WallpaperSetterApp(QMainWindow):
    BG_COLOR = "#2d2d2d"
    FG_COLOR = "#ffffff"
    FONT_FAMILY = "Meiryo"  # メイリオに設定

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ライセンス認証無いときに使うやつ")
        self.setGeometry(100, 100, 320, 360)
        self.setFixedSize(320, 360)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ボタン（壁紙適用だけ青、それ以外灰色）
        self.dark_mode_btn = self._create_styled_button("ダークモード", lambda: self.handle_mode_switch(True), gray=True)
        self.light_mode_btn = self._create_styled_button("ライトモード", lambda: self.handle_mode_switch(False), gray=True)
        self.choose_wallpaper_btn = self._create_styled_button("壁紙を選択", self.choose_wallpaper, gray=True)
        self.apply_wallpaper_btn = self._create_styled_button("壁紙適用", self.apply_wallpaper, gray=False)

        # 壁紙パス表示ラベル
        self.wallpaper_path_label = QLabel("壁紙が選択されていません", self)
        self.wallpaper_path_label.setStyleSheet(f"""
            QLabel {{
                color: {self.FG_COLOR};
                background-color: #3c3c3c;
                padding: 8px;
                border: 1px solid #555555;
                border-radius: 5px;
                min-height: 24px;
                font-family: {self.FONT_FAMILY};
            }}
        """)
        self.wallpaper_path_label.setAlignment(Qt.AlignCenter)

        # レイアウト追加
        main_layout.addWidget(self.dark_mode_btn)
        main_layout.addWidget(self.light_mode_btn)
        main_layout.addSpacing(8)
        main_layout.addWidget(self.choose_wallpaper_btn)
        main_layout.addWidget(self.wallpaper_path_label)
        main_layout.addWidget(self.apply_wallpaper_btn)
        main_layout.addStretch(1)

        self.wallpaper_path = ""

        # ウィンドウ全体の背景色とフォントを設定
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.BG_COLOR};
                font-family: {self.FONT_FAMILY};
                color: {self.FG_COLOR};
            }}
        """)

    def _create_styled_button(self, text, handler, gray=True):
        """壁紙適用だけ青 (#0078d4)、その他は灰色 (#555555)"""
        button = QPushButton(text, self)
        button.setMinimumHeight(44)
        button.clicked.connect(handler)
        color = "#0078d4" if not gray else "#555555"
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-family: {self.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {QColor(color).darker(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(color).darker(150).name()};
                border-style: inset;
            }}
        """)
        return button

    def handle_mode_switch(self, dark):
        success, message = set_dark_mode(dark)
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "エラー", message)

    def choose_wallpaper(self):
        # 画像ファイルのみにフィルタを適用
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "壁紙を選択",
            "",
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.wallpaper_path_label.setText(os.path.basename(file_path))
            self.wallpaper_path = file_path
        else:
            self.wallpaper_path_label.setText("壁紙が選択されていません")
            self.wallpaper_path = ""

    def apply_wallpaper(self):
        if self.wallpaper_path:
            success, message = set_wallpaper(self.wallpaper_path)
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "Error", message)
        else:
            QMessageBox.warning(self, "Warning", "壁紙を選択してください")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WallpaperSetterApp()
    window.show()
    sys.exit(app.exec_())