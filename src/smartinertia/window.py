import logging
from typing import Optional

from PyQt5.QtCore import QSettings, QSize, QTimer
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QAction, QLabel, QMainWindow, QMessageBox

from smartinertia import __version__
from smartinertia.conn_thread import ConnectionThread
from smartinertia.connection import Connection
from smartinertia.data import Data
from smartinertia.dialogs import ConnectionDialog, RunDialog
from smartinertia.graph import BarPlotWidget

log = logging.getLogger(__name__)

BAUD = 115200


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings):
        super().__init__()
        self.setGeometry(50, 50, 800, 500)
        self.setMinimumSize(800, 500)
        self.setWindowTitle(f'Smart Inertia - v{__version__}')
        self.setWindowIcon(QIcon("icon.png"))

        self.connection = None  # type: Optional[Connection]
        self.connection_port = None  # type: Optional[str]
        self.connection_thread = None  # type: Optional[ConnectionThread]

        self.settings = settings

        log.info("Initialize menu bar.")
        self._init_menu()
        log.info("Initialize graph.")
        self._init_graph()

    def _init_graph(self):
        self.data = Data(self)
        # BarPlotWidget uses Data as a queue from serial
        self.graph = BarPlotWidget(self.data)
        self.setCentralWidget(self.graph)

        # periodically update graph according to new data
        self.graph_update_timer = QTimer()
        self.graph_update_timer.timeout.connect(self.graph.update_graph)
        self.graph_update_timer.setInterval(16)  # 60 FPS

    def _init_menu(self):
        menu_bar = self.menuBar()

        start_action = QAction('Start', self)
        start_action.triggered.connect(self.start)
        menu_bar.addAction(start_action)

        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(self.stop)
        menu_bar.addAction(stop_action)

        connection_action = QAction('Connect', self)
        connection_action.triggered.connect(self.connect)
        menu_bar.addAction(connection_action)

        # add a spinning gif to show when a device is connected
        connected_gif = QMovie("loading.gif")
        connected_gif.start()
        self.connected_label = QLabel("abc")
        self.connected_label.setMargin(1.5)
        label_size = self.connected_label.sizeHint()
        connected_gif.setScaledSize(QSize(label_size.height(), label_size.height()))
        self.connected_label.setMovie(connected_gif)
        self.connected_label.hide()
        menu_bar.setCornerWidget(self.connected_label)

    def start(self):
        log.info("Start button clicked!")

        # stop updating graph
        self.graph_update_timer.stop()

        # close existing thread and connection
        self._close_connection()

        # clear data from previous run
        self.data.clear()
        self.graph.clear_graph()

        if self.connection_port is None:
            log.info("Connection port was not setup. Open connection dialog.")
            self.connect()
            if self.connection_port is None:
                log.info("Connection port was not setup a second time.")
                return

        run_dialog = RunDialog(self)
        run_dialog.exec_()
        if run_dialog.run_conf is None:
            log.info("Start dialog not accepted.")
            return
        else:
            self.data.set_run_conf(run_dialog.run_conf)

        # setup new connection
        try:
            self.connection = Connection(self.connection_port, baud=BAUD)
            self.connection.open()
        except:
            self.connection = None
            QMessageBox.warning(self, "Connection failed!",
                                "Cannot connect to flywheel!\nTry reconnecting USB and/or restarting software.")
            log.exception(f"Connection to {self.connection_port} could not be established!")
            return

        # ConnectionThread continuously reads from the serial port and sends incoming data to Data
        self.connection_thread = ConnectionThread(self.connection, self.data.add_new)
        self.connection_thread.start()
        log.info("Connection thread started.")

        # start updating graph
        self.graph_update_timer.start()
        self.connected_label.show()
        if run_dialog.run_conf.target_check:
            self.graph.add_target_line(run_dialog.run_conf.target_value)

    def stop(self):
        log.info("Stop button clicked!")

        # stop updating graph
        self.graph_update_timer.stop()
        self.connected_label.hide()

        # stop and remove connection and threads
        self._close_connection()

        # save and show report
        self.data.report()

    def connect(self):
        log.info("Connect button clicked!")

        # clear port to not interfere with new connection
        self.connection_port = None

        conn_dialog = ConnectionDialog(self)
        conn_dialog.exec_()

        if conn_dialog.conn_conf is None:
            log.info("Connection dialog not accepted.")
        elif not conn_dialog.conn_conf.port:
            log.info("No connections available.")
        else:
            self.connection_port = conn_dialog.conn_conf.port

        if self.connection_port is None:
            QMessageBox.warning(self, "No connection!",
                                "No connection was established!")

    def _close_connection(self):
        if self.connection_thread is not None:
            # threads are like women, you can't just tell them to stop
            # you can only suggest it and then hope for the best
            self.connection_thread.stop = True
            log.info("Connection thread stopped.")

        if self.connection is not None:
            # close and delete connection
            self.connection.close()
            self.connection = None
            log.info("Connection closed.")

    def closeEvent(self, a0):
        log.info("Closing window. Doing cleanup.")
        self.graph_update_timer.stop()
        self._close_connection()
        self.graph.deleteLater()
        log.info("Cleanup successful.")
