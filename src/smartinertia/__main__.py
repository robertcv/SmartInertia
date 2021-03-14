import logging
import sys
import traceback
from unittest.mock import patch

import pyqtgraph as pg
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from smartinertia import __version__
from smartinertia.window import MainWindow

log = logging.getLogger(__name__)

# logging configuration
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# pyqtgraph color configuration
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


def excepthook(exc_type, exc_value, exc_tb):
    """Handle exceptions that don't occur in the main thread."""
    log.error("Exception in outside main thread!")
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log.error(tb)
    QApplication.quit()


def main():
    # setup settings
    setting = QSettings('SmartInertia', __version__)

    # start the application
    log.info("Opening the main window.")
    app = QApplication(sys.argv)
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
