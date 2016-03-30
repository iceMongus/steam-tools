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

import os, sys
from time import sleep
from logging import getLogger
from ctypes import CDLL

LOGGER = getLogger('root')

if os.name == 'nt':
    ext = '.dll'
else:
    ext = '.so'

if sys.maxsize > 2**32:
    STEAM_API = 'lib64/libsteam_api' + ext
else:
    STEAM_API = 'lib32/libsteam_api' + ext

if not os.path.isfile(STEAM_API):
    libDir = '/share/steam-tools'
    if os.path.isfile(os.path.join('/usr/local', libDir, STEAM_API)):
        STEAM_API = os.path.join('/usr/local', libDir, STEAM_API)
    elif os.path.isfile(os.path.join('/usr', libDir, STEAM_API)):
        STEAM_API = os.path.join('/usr', libDir, STEAM_API)
    else:
        LOGGER.critical("I cannot find the SteamAPI. Please, verify your installation.", file=sys.stderr)
        sys.exit(1)

STEAM_API = CDLL(STEAM_API)

def fakeIt(appid):
    os.environ["SteamAppID"] = appid

    if STEAM_API.SteamAPI_IsSteamRunning():
        if not STEAM_API.SteamAPI_Init():
            return 2
        return 0
    else:
        return 1

def close():
    os.environ.pop("SteamAppID")
    STEAM_API.SteamAPI_Shutdown()
    ####
    # STUB
    sleep(10)
    ####
    # FIXME: How I can actually stop the SteamAPI?
    # When Init() is called, the SteamAPI
    # is running with the current PID, and the
    # Steam will wait until this PID stops. The
    # problem is that the current process is the
    # main process of SteamTools and it'll not stop.
    #
    # This implis that, if the steam library was
    # used as a module, it will not function properly
    # without a different process for execute.
    #
    # Thus, this work is frozen.
    #####