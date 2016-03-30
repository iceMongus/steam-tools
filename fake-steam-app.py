#!/usr/bin/env python
#
# Lara Maia <dev@lara.click> 2015
#
# The Steam Tools is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# The Steam Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#

import sys
from time import sleep
from datetime import timedelta
from signal import signal, SIGINT

from stlib import stlogger
from stlib import stlibsteam

LOGGER = stlogger.getLogger()

def signal_handler(signal, frame):
    LOGGER.info("Exiting...")
    stlibsteam.close()
    sys.exit(0)

if __name__ == "__main__":
    signal(SIGINT, signal_handler)

    if len(sys.argv) < 2:
        LOGGER.critical("Hello~wooooo. Where is the game ID?")
        sys.exit(1)

    ret = stlibsteam.fakeIt(sys.argv[1])
    
    if not ret:
        LOGGER.info("Game started.")
        c = 1
        while True:
            stlogger.cmsg("Playing {} for {} seconds".format(sys.argv[1], timedelta(seconds=c)), end='\r')
            sleep(1)
            c += 1
    elif ret == 1:
        LOGGER.critical("I cannot find a Steam instance.")
        LOGGER.critical("Please, check if your already start your steam client.")
        sys.exit(ret)
    elif ret == 2:
        LOGGER.critical("I cannot find a game with that ID (%s). Exiting.", sys.argv[1])
        sys.exit(ret)
    else:
        sys.exit(ret)
