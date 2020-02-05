#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tracks active window, keystrokes and mouse clicks
"""

import sys
import json
import shutil
import pyxhook
from pynput.mouse import Listener
import os
import re
import subprocess
import time
import threading
import argparse
import logging

LOGGER = logging.getLogger(__name__)


# fmt: off
def comandline_argument_parser(parser=None):
    if not parser:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    if __name__ == "__main__":
        parser.add_argument("--loggers", nargs="*", default=[__name__], help="Changes the logging level of all the given loggers. 'root' is the global logger and __name__  is logger of this script")
        parser.add_argument("--logging-level", default="info", choices=["notset", "debug", "info", "warning", "error", "critical"], help="Logging level")
        parser.add_argument("--logging-file", help="Logging file name")
    return parser
# fmt: on

#######################################################################
#                          activity tracking                          #
#######################################################################


def get_active_window_title():
    root = subprocess.Popen(["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE)
    stdout, stderr = root.communicate()

    m = re.search(b"^_NET_ACTIVE_WINDOW.* ([\w]+)$", stdout)
    if m is not None:
        window_id = m.group(1)
        window = subprocess.Popen(["xprop", "-id", window_id, "WM_NAME"], stdout=subprocess.PIPE)
        stdout, stderr = window.communicate()
    else:
        return None

    match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
    if match is not None:
        return match.group("name").strip(b'"').decode("UTF-8")

    return None


def activitySaver(sleepIntervall=10):
    while True:
        LOGGER.info(get_active_window_title() + " ; sleepIntervall= %s", str(sleepIntervall))
        time.sleep(sleepIntervall)


#######################################################################
#                         key press tracking                          #
#######################################################################


class keyboardKeys:
    """description"""

    def __init__(self, dataFile):
        self.keys = {}
        self.dataFile = dataFile
        self.readDataFile()
        if os.path.isfile(self.dataFile):
            shutil.copy(self.dataFile, self.dataFile.replace(".json", "_backup.json"))

    def writeDataFile(self):
        LOGGER.info("Saving to " + self.dataFile)
        with open(self.dataFile, "w") as dFile:
            dFile.write(json.dumps(self.keys))

    def readDataFile(self):
        if not os.path.isfile(self.dataFile):
            LOGGER.warning(
                self.dataFile
                + " not found! This is expected if it is the first time using this script."
            )
            return
        with open(self.dataFile, "r") as dFile:
            self.keys = json.load(dFile)

    def OnKeyPress(self, event):
        key = event.Key
        if key in self.keys:
            self.keys[key] += 1
        else:
            self.keys[key] = 1
        # NOTE you don't want to save each key in order since this would be a secrutiy risk as it would also save passwords in plain text
        # LOGGER.info(event.Key)
        LOGGER.info("key press")

    def record(self, sleepIntervall):
        while True:
            time.sleep(sleepIntervall)
            self.writeDataFile()


def keyLogger(keyData):
    keys = keyboardKeys(keyData)
    new_hook = pyxhook.HookManager()
    new_hook.KeyDown = keys.OnKeyPress
    new_hook.HookKeyboard()
    new_hook.start()
    keys.record(10)


#######################################################################
#                           mouse tracking                            #
#######################################################################


def on_move(x, y):
    # print("Pointer moved to {0}".format((x, y)))
    pass


def on_click(x, y, button, pressed):
    LOGGER.info("{0} at {1}".format("Pressed" if pressed else "Released", (x, y)))


def on_scroll(x, y, dx, dy):
    # print("Scrolled {0}".format((x, y)))
    pass


#######################################################################
#                                main                                 #
#######################################################################


def main(args):

    activityThread = threading.Thread(target=activitySaver, args=(10,))
    activityThread.start()

    keyLoggerThread = threading.Thread(target=keyLogger, args=("keyData.json",))
    keyLoggerThread.start()

    mouseThread = Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    mouseThread.start()


if __name__ == "__main__":
    parser = comandline_argument_parser()
    command_line_arguments = parser.parse_args()
    logging.basicConfig(
        filename=command_line_arguments.logging_file,
        format="%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s() - %(asctime)s ]: %(message)s",
    )
    logLevel = getattr(logging, command_line_arguments.logging_level.upper())
    for logger in command_line_arguments.loggers:
        if logger == "root":
            tmpLOGGER = logging.getLogger()
        else:
            tmpLOGGER = logging.getLogger(logger)
        tmpLOGGER.setLevel(logLevel)
    LOGGER.info(command_line_arguments)
    sys.exit(main(command_line_arguments))