# SPDX-FileCopyrightText: 2022 Coop IT Easy SCRLfs
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import re

import serial

from .scale_driver import AbstractScaleDriver, ScaleConnectionError

ANSWER_RE = re.compile(rb"^\?(?P<status>.)|(?P<weight>\d+\.\d+)$")

_logger = logging.getLogger(__name__)


class MettlerToledo8217ScaleDriver(AbstractScaleDriver):
    """Driver for the 8217 Mettler Toledo protocol. Because of Python
    restrictions, the number doesn't come first in the class name.
    """

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.vendor_product = "mettler_toledo_8217"
        self._poll_interval = self.config.getfloat(
            "scale_driver", "poll_interval", fallback=0.2
        )

    @property
    def poll_interval(self):
        return self._poll_interval

    @property
    def _port(self):
        return self.config.get("scale_driver", "port", fallback="/dev/ttyS0")

    @property
    def _baudrate(self):
        return self.config.getint("scale_driver", "baudrate", fallback=9600)

    def acquire_data(self, connection):
        """Acquire data over the connection."""
        buffer = b""
        stx = False
        # ask for weight data
        try:
            connection.write(b"W")
        except serial.SerialException as e:
            raise ScaleConnectionError() from e
        while True:
            try:
                c = connection.read(1)
            except serial.SerialException as e:
                raise ScaleConnectionError() from e
            if not c:
                # timeout
                raise serial.SerialTimeoutException()
            if c == b"\x02":
                # start of answer
                stx = True
                buffer = b""
            elif c == b"\r":
                # end of answer
                if not stx:
                    continue
                break
            else:
                buffer += c
        match = ANSWER_RE.match(buffer)
        if match is None:
            raise ValueError("serial readout was not valid")
        matchdict = match.groupdict()
        _logger.debug(matchdict)
        status = matchdict["status"]
        weight = matchdict["weight"]
        with self.data_lock:
            result = self.data.copy()
        if weight is not None:
            result.update({"value": float(weight), "status": "ok"})
            return result
        if not isinstance(status, bytes):
            return result
        status_byte = int.from_bytes(status, byteorder="big")
        if status_byte & 0b1:
            # in motion
            result.update({"status": "moving"})
        elif status_byte & 0b110:
            # FIXME: Find a better status.
            result.update({"status": "error"})
        return result

    def establish_connection(self):
        """Establish a connection. The connection must be a context manager."""
        return serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.SEVENBITS,
            timeout=1,
        )
