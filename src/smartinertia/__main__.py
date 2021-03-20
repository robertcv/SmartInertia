import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from unittest.mock import patch

import pyqtgraph as pg
from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtWidgets import QApplication

from smartinertia import __version__
from smartinertia.window import MainWindow

# logging configuration
log = logging.getLogger("smartinertia")
log.setLevel(logging.INFO)

# logging to std out
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)


def setup_file_logging():
    """Setup logging into files."""
    log_dir = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
    log_path = os.path.join(log_dir, "smartinertia.log")
    log.info(f"Log file location: {log_path}")

    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            log.info(f"Created log dir.")
        except PermissionError:
            log.exception(f"Could not create log dir.")

    try:
        fh = RotatingFileHandler(log_path, maxBytes=int(1e7), backupCount=5)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    except (PermissionError, FileNotFoundError):
        log.exception(f"Could not open log file.")


# pyqtgraph color configuration
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


def excepthook(exc_type, exc_value, exc_tb):
    """Handle exceptions that don't occur in the main thread."""
    log.error("Exception outside main thread!")
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log.error(tb)
    QApplication.quit()


def main():
    # start the application
    log.info("Launching application.")
    app = QApplication(sys.argv)
    app.setApplicationName("SmartInertia")

    # setup logging to file
    setup_file_logging()

    # setup settings
    log.info("Opening settings.")
    setting = QSettings('SmartInertia', __version__)
    log.info(f"Settings location: {setting.fileName()}.")

    log.info("Opening the main window.")
    gui = MainWindow(setting)
    gui.show()
    try:
        with patch('sys.excepthook', excepthook):
            app.exec_()
    except:
        log.exception("Exception in main thread!")
    log.info("Close the main window.")


if __name__ == '__main__':
    main()
