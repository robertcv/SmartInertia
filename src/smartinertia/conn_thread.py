import logging
from typing import Callable

from PyQt5.QtCore import QThread, pyqtSignal

from smartinertia.connection import Connection

log = logging.getLogger(__name__)


class ConnectionThread(QThread):
    """This thread reads data send over serial and sends it to gui."""
    sig = pyqtSignal(tuple)

    def __init__(self, con: Connection, sig_receiver: Callable) -> None:
        super().__init__()
        self.con = con
        self.sig.connect(sig_receiver)
        self.stop = False
        log.info("Create connection thread.")

    def run(self):
        """This function is run when the thread starts. The thread stops if this function returns."""
        while not self.stop:
            try:
                line = self.con.readline()
                t, f = line.split(b',')
                self.sig.emit((float(t), float(f)))
            except:
                pass
