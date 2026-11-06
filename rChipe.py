#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.qt_compat import QtWidgets, QT_API
from ui.main_window import MainWindow


def main():
    if "QT_QPA_PLATFORMTHEME" not in os.environ and sys.platform.startswith("linux"):
        pass

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("rChipe")
    app.setOrganizationName("CortexRevolution")

    print(f"[+] Starting rChipe with Qt backend: {QT_API}")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
