#!/usr/bin/env python
#
# Lara Maia <dev@lara.click> 2015 ~ 2016
#
# The Steam Tools is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#k
# The Steam Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#

import os
import tempfile
import sqlite3
import json
from shutil import copy, rmtree
from logging import getLogger

from stlib import stconfig

LOGGER = getLogger('root')
CONFIG = stconfig.getParser()

if os.name == 'nt':
    from ctypes import *
    from ctypes.wintypes import DWORD
    localfree = windll.kernel32.LocalFree
    memcpy = cdll.msvcrt.memcpy
    CryptUnprotectData = windll.crypt32.CryptUnprotectData

    class DATA_BLOB(Structure):
        _fields_ = [
                ("cbData", DWORD),
                ("pbData", POINTER(c_char))
            ]

    # Thanks to Crusher Joe (crusherjoe <at> eudoramail.com)
    # Adapted from here: http://article.gmane.org/gmane.comp.python.ctypes/420
    def win32CryptUnprotectData(edata):
        bufferIn = c_buffer(edata, len(edata))
        blobIn = DATA_BLOB(len(edata), bufferIn)
        blobOut = DATA_BLOB()

        if CryptUnprotectData(byref(blobIn), None, None, None, None, 0x01, byref(blobOut)):
            cbData = int(blobOut.cbData)
            pbData = blobOut.pbData
            buffer = c_buffer(cbData)
            memcpy(buffer, pbData, cbData)
            localfree(pbData);
            return buffer.raw
        else:
            return ""
else:
    # pycrypto
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Cipher import AES

def sqlConn(profile, url):
    cookies = {}
    tempDir = tempfile.mkdtemp()
    cookiesPath = os.path.join(profile, 'Cookies')
    temp_cookiesPath = os.path.join(tempDir, os.path.basename(cookiesPath))
    copy(cookiesPath, temp_cookiesPath)

    connection = sqlite3.connect(temp_cookiesPath)
    query = 'SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE ?'
    for key, data, edata in connection.execute(query, (getDomainName(url),)):
        if key == '_ga': continue
        if edata[:3] != b'v10' and edata[:3] != b'\x01\x00\x00':
            if data:
                cookies[key] = data
            else:
                cookies[key] = edata
        else:
            cookies[key] = decryptData(edata)
    connection.close()

    rmtree(tempDir)

    return cookies

def getChromeProfile(url):
    if os.name == 'nt':
        dataDir = os.getenv('LOCALAPPDATA')
        chromeDir = os.path.join(dataDir, 'Google/Chrome/User Data')
        # Fallback to Chromium
        if not os.path.isdir(chromeDir):
            chromeDir = os.path.join(dataDir, 'Chromium/User Data')
    else:
        dataDir = os.getenv('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
        chromeDir = os.path.join(dataDir, 'google-chrome')
        # Fallback to Chromium
        if not os.path.isdir(chromeDir):
            chromeDir = os.path.join(dataDir, 'chromium')

    profiles = []
    if os.path.isdir(chromeDir):
        for dirName in sorted(os.listdir(chromeDir)):
            if 'Profile' in dirName or 'Default' in dirName:
                if os.path.isfile(os.path.join(chromeDir, dirName, 'Cookies')):
                    profiles.append(os.path.join(chromeDir, dirName))

    if not len(profiles):
        LOGGER.error("I cannot find your Chrome/Chromium profile")
        return None
    elif len(profiles) == 1:
        return profiles[0]
    else:
        profile = os.path.join(chromeDir, CONFIG.get('Config', 'chromeProfile', fallback='Default'))
        if os.path.isfile(os.path.join(profile, 'Cookies')):
            if "steampowered" or "steamcommunity" in url:
                if "steamLogin" in sqlConn(profile, url):
                    return profile
                else:
                    LOGGER.error("I don't find steam cookies in the current profile")
            else:
                return profile

        LOGGER.warning(" Who are you?")
        for i in range(len(profiles)):
            with open(os.path.join(profiles[i], 'Preferences')) as prefs_file:
                prefs = json.load(prefs_file)

            try:
                profileName = prefs['account_info'][0]['full_name']
            except KeyError:
                profileName = prefs['profile']['name']

            LOGGER.warning('  - [%d] %s (%s)',
                        i+1,
                        profileName,
                        os.path.basename(profiles[i]))

        while True:
            try:
                opc = int(input("Please, input an number [1-{}]:".format(len(profiles))))
                if opc > len(profiles) or opc < 1:
                    raise(ValueError)
            except ValueError:
                LOGGER.error('Please, choose an valid option.')
                continue
            LOGGER.warning("Okay, I'm remember that.")
            break

        return profiles[opc-1]

def decryptData(edata):
    if os.name == 'nt':
        return win32CryptUnprotectData(edata).decode('utf-8')
    else:
        cipher = AES.new(PBKDF2(b'peanuts', b'saltysalt', 16, 1), AES.MODE_CBC, IV=b' '*16)
        decrypted = cipher.decrypt(edata[3:])
        return decrypted[:-decrypted[-1]].decode('utf-8')

def getDomainName(url):
    site = url.split('//', 1)[1].split('/', 1)[0].split('.')
    if len(site) > 2 and site[-3] == 'www':
        return '.'+'.'.join(site[-2:])
    else:
        if len(site) > 2:
            return '.'.join(site[-3:])
        else:
            return '.'.join(site[-2:])

def getCookies(url):
    profile = getChromeProfile(url)

    if profile:
        CONFIG.set('Config', 'chromeProfile', os.path.basename(profile))
        stconfig.write()
    else:
        return {}

    return sqlConn(profile, url)
