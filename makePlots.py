#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create plots from the data base
TODO:
    activity pie chart per day/week/year
    allow to categorize activities (changes day to day week to week)
    activity probability as when over the day do i do this
    switching applications
    special activity 'browsing'. Create breakdown just for this?
    keyboard/mouse click activity over time (per minute/hour/day/week)

    does not need data base
        keyboard heat map
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import timeTracker
import sys
import argparse
import logging

LOGGER = logging.getLogger(__name__)


# fmt: off
def comandline_argument_parser(parser=None):
    if not parser:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    if __name__ == "__main__":
        parser.add_argument("--loggers", nargs="*", default=[__name__], help="Changes the logging level of all the given loggers. 'root' is the global logger and __name__  is logger of this script")
        parser.add_argument("--logging-level", default="warning", choices=["notset", "debug", "info", "warning", "error", "critical"], help="Logging level")
        parser.add_argument("--logging-file", help="Logging file name")
    return parser
# fmt: on


class logFileParser:
    """Class to parse the information saved in the log file created by timeTracker"""

    def __init__(self):
        self.keyPresses = []
        self.mouseClicks = []
        self.activities = {}

    def parseLogFile(self, fileName):
        with open(fileName, "r") as lFile:
            # INFO [timeTracker.py:119 - OnKeyPress() - 2020-02-06 13:59:27,945 ]: key press
            # INFO [timeTracker.py:77 - activitySaver() - 2020-02-06 13:59:32,217 ]: termite # tmux ; sleepIntervall= 10
            # INFO [timeTracker.py:77 - activitySaver() - 2020-02-06 13:59:02,151 ]: brave-browser # Ht condor submission (!41) · Merge Requests · ATLAS Physics / EXOT / JDM / ANA-EXOT-2018-46 / MonoHbbTruthFramework_NtupleToHist · GitLab - Brave ; sleepIntervall= 10
            # INFO [timeTracker.py:147 - on_click() - 2020-02-06 13:59:22,164 ]: Released at (2009, 13)
            for li in lFile:
                if "OnKeyPress" in li:
                    self.keyPresses.append(li[42:61])
                elif "on_click" in li:
                    self.mouseClicks.append(li[40:59])
                elif "activitySaver" in li:
                    timeStamp = li[44:63]
                    cls = li[li.find("]:") + 3 : li.find("#") - 1]
                    # name=li[li.find("#")+2:li.find(";")-1]
                    # tmp=li[li.find("=")+2:]
                    # sleepI=tmp[:tmp.find(" ")]
                    if not cls in self.activities:
                        self.activities[cls] = []
                    # if not name in self.activities[cls]:
                    # self.activities[cls][name]=[]
                    self.activities[cls].append(timeStamp)
                else:
                    LOGGER.debug("This line will not be recorded:\n" + li)


def plotKeys(keys: list):
    npKeys = np.array(keys)
    index = pd.DatetimeIndex(npKeys)
    data = pd.DataFrame(data=[1] * len(index), index=index, columns=["hits"])
    data = data.groupby(lambda x: x.hour)
    data = data.agg({"hits": sum})
    sns.set(rc={"figure.figsize": (11, 4)})
    fig, ax = plt.subplots()
    data["hits"].plot(linewidth=0.5)
    # sns.boxplot(data=data, x='day', y=0, ax=ax)
    # sns.boxplot(data=data, y="hits", ax=ax)
    plt.show()


def main(args):
    lFileParser = logFileParser()
    lFileParser.parseLogFile(timeTracker.LOGFILE)
    plotKeys(lFileParser.keyPresses)


if __name__ == "__main__":
    parser = comandline_argument_parser()
    command_line_arguments = parser.parse_args()
    logging.basicConfig(
        filename=command_line_arguments.logging_file,
        format="%(levelname)s [%(filename)s:%(lineno)s - %(funcName)s() ]: %(message)s",
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
