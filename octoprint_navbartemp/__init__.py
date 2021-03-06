# coding=utf-8
from __future__ import absolute_import

__author__ = "Jarek Szczepanski <imrahil@imrahil.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 Jarek Szczepanski - Released under terms of the AGPLv3 License"

import octoprint.plugin
from octoprint.util import RepeatedTimer
import sys
import re

class NavBarPlugin(octoprint.plugin.StartupPlugin,
                   octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.isRaspi = False
        self.isSOC = False
        self.debugMode = False      # to simulate temp on Win/Mac
        self.displayRaspiTemp = True
        self._checkTempTimer = None

    def on_after_startup(self):
        self.displayRaspiTemp = self._settings.get(["displayRaspiTemp"])
        self._logger.debug("displayRaspiTemp: %s" % self.displayRaspiTemp)

        if self.debugMode:
            self.isRaspi = True
            if self.displayRaspiTemp:
                self.startTimer(5.0)
        elif sys.platform == "linux2":
            with open('/proc/cpuinfo', 'r') as infile:
                    cpuinfo = infile.read()
            # Match a line like 'Hardware   : BCM2709'
            match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)
            self._logger.debug("Hardware: %s", match.group(1))

            if match is None:
                # Couldn't find the hardware, assume it isn't a pi.
                self.isRaspi = False
            elif match.group(1) == 'BCM2708':
                self._logger.debug("Pi 1")
                self.isRaspi = True
            elif match.group(1) == 'BCM2709':
                self._logger.debug("Pi 2")
                self.isRaspi = True
            elif match.group(1) == 'sun50iw1p1':
                self._logger.debug("Pine A64")
                self.isSOC = True

            if (self.isRaspi or self.isSOC) and self.displayRaspiTemp:
                self._logger.debug("Let's start RepeatedTimer!")
                self.startTimer(30.0)

        self._logger.debug("is Raspberry Pi? - %s" % self.isRaspi)

    def startTimer(self, interval):
        self._checkTempTimer = RepeatedTimer(interval, self.checkRaspiTemp, None, None, True)
        self._checkTempTimer.start()

    def checkRaspiTemp(self):
        self._logger.info("Checking Raspberry Pi internal temperature")

        if self.debugMode:
            import random
            def randrange_float(start, stop, step):
                return random.randint(0, int((stop - start) / step)) * step + start
            p = "temp=%s'C" % randrange_float(5, 60, 0.1)

        elif sys.platform == "linux2":
            if self.isRaspi:
                from sarge import run, Capture
                p = run("cat /etc/armbianmonitor/datasources/soctemp", stdout=Capture())
                if p.returncode==1:
                    self.isRaspi = False
                    self._logger.error("SoC temperature not found.")
                else:
                    p = p.stdout.text
                    self._logger.debug("response from sarge: %s" % p)
                    match = re.search('=(.*)\'', p)

            elif self.isSOC:
                self._logger.debug("Reading /sys/devices/virtual/thermal/thermal_zone0/temp")
                with open('/sys/devices/virtual/thermal/thermal_zone0/temp', 'r') as content_file:
                    p = content_file.read()
                self._logger.debug("Read: %s" % p)
                match = re.search('(\d+)', p)

        if not match:
            self._logger.error("Invalid temperature format.")
            self.isRaspi = False
            self.isSOC = False
        else:
            temp = match.group(1)
            self._logger.debug("Temperature: %s" % temp)
            self._plugin_manager.send_plugin_message(self._identifier, dict(israspi=self.isRaspi, issoc=self.isSOC, raspitemp=temp))


	##~~ SettingsPlugin
    def get_settings_defaults(self):
        return dict(displayRaspiTemp = self.displayRaspiTemp)

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        self.displayRaspiTemp = self._settings.get(["displayRaspiTemp"])

        if self.displayRaspiTemp:
            interval = 5.0 if self.debugMode else 30.0
            self.startTimer(interval)
        else:
            if self._checkTempTimer is not None:
                try:
                    self._checkTempTimer.cancel()
                except:
                    pass
            self._plugin_manager.send_plugin_message(self._identifier, dict())

	##~~ TemplatePlugin API
    def get_template_configs(self):
        if self.isRaspi or self.isSOC:
            return [
                dict(type="settings", template="navbartemp_settings_raspi.jinja2")
            ]
        else:
            return []

    ##~~ AssetPlugin API
    def get_assets(self):
        return {
            "js": ["js/navbartemp.js"],
            "css": ["css/navbartemp.css"],
            "less": ["less/navbartemp.less"]
        } 

    ##~~ Softwareupdate hook
    def get_update_information(self):
        return dict(
            navbartemp=dict(
                displayName="Navbar Temperature Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="JeffyW",
                repo="OctoPrint-NavbarTemp",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/JeffyW/OctoPrint-NavbarTemp/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "Navbar Temperature Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = NavBarPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
