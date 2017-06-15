from __future__ import absolute_import

__author__ = "Jeff Wight <jeffyw@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Jeff Wight"


import octoprint.plugin
from octoprint.util import RepeatedTimer
import sys
import re

class SystemStats(octoprint.plugin.StartupPlugin):

    def __init__(self):
        self._timer = None
        
        self.debugMode = False
        self.hardware = None
        
        self.tempFunc = None

    def on_after_startup(self):
        if self.debugMode:
            self.hardware = "Debug"
        elif sys.platform.startswith("linux2"):
            with open("/proc/cpuinfo", "r") as infile:
                cpuinfo = infile.read()

            # Match a line like "Hardware   : BCM2709"
            match = re.search("^Hardware\s+:\s+(\w+)$", cpuinfo, flags=re.MULTILINE | re.IGNORECASE)

            if match is not None:
                self.hardware = match.group(1)
                self._logger.debug("Hardware: %s", self.hardware)

            from os.path import isFile
            if isFile("/sys/devices/virtual/thermal/thermal_zone0/temp"):
                self.tempFunc = temp_from_thermal

                self.hardware_overrides()
            self.start_timer(5.0)

    def start_timer(self, interval):
        self._logger.debug("Starting RepeatedTimer with interval: %d" % interval)
        self._timer = RepeatedTimer(interval, self.get_stats, run_first=True)
        self._timer.start()

    def get_system_stats(self):
        self._logger.info("Collecting system stats.")

        if self.debugMode:
            temp = randrange_float(5, 60, 0.1)
        elif self.tempFunc is not None:
            temp = self.tempFunc()

        self._plugin_manager.send_plugin_message(self._identifier, dict(temp=temp))

    def hardware_overrides(self):
        if self.hardware == "BCM2708":
            self._logger.debug("Pi 1")
            self.tempFunc = temp_from_vcgencmd
        elif self.hardware == "BCM2709":
            self._logger.debug("Pi 2")
            self.tempFunc = temp_from_vcgencmd
        elif self.hardware == "sun50iw1p1":
            self._logger.debug("Pine A64")
    
    def temp_from_thermal(self):
        self._logger.debug("Reading: /sys/devices/virtual/thermal/thermal_zone0/temp")
        with open("/sys/devices/virtual/thermal/thermal_zone0/temp", "r") as content_file:
            p = content_file.read()
        self._logger.debug("Temperature: %s" % p)
        return p

    def temp_from_vcgencmd(self):
        self._logger.debug("Running: /opt/vc/bin/vcgencmd measure_temp")
        temp = None
        from sarge import run, Capture
        p = run("/opt/vc/bin/vcgencmd measure_temp", stdout=Capture())
        if p.returncode==1:
            self._logger.error("Command failed.")
        else:
            p = p.stdout.text
            self._logger.debug("Command output: %s" % p)
            match = re.search("=(.*)\'", p)
            if not match:
                self._logger.error("Invalid temperature format.")
            else:
                temp = match.group(1)
                self._logger.debug("Temperature: %s" % temp)
        return temp

    def randrange_float(start, stop, step):
        import random
        return random.randint(0, int((stop - start) / step)) * step + start

__plugin_name__ = "Server Stats Plugin"
