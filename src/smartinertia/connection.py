import logging
import os
from time import sleep

from serial import Serial
from serial.tools.list_ports import grep

log = logging.getLogger(__name__)


def get_ports():
    """Get available serial connections."""
    serial_ports = []
    if os.name == 'nt':
        serial_ports = list(grep(r'COM*'))
    elif os.name == 'posix':
        serial_ports = list(grep(r'USB*'))
    log.info(f"Current OS name {os.name}.")

    serial_ports = [p.device for p in serial_ports]
    log.info(f"Available serial ports: {','.join(serial_ports)}.")

    return serial_ports


class Connection:
    """Object to hold the serial connection."""
    def __init__(self, port, baud=9600, timeout=1):
        self.ser = Serial()
        self.ser.port = port
        self.ser.baudrate = baud
        self.ser.timeout = timeout
        log.info(f"Create connection to {port} with {baud}.")

    def open(self):
        self.ser.open()
        sleep(0.1)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        log.info(f"Open connection to {self.ser.port}.")

    def readline(self):
        l = self.ser.readline()
        while not l:
            l = self.ser.readline()
        return l

    def close(self):
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
        except:
            log.exception("Failed to close connection!")
        log.info(f"Close connection to {self.ser.port}.")


if __name__ == '__main__':
    print(get_ports())
