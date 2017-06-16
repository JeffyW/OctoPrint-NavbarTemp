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
        self.displayRaspiTemp = True

	##~~ SettingsPlugin
    def get_settings_defaults(self):
        return dict(displayRaspiTemp = self.displayRaspiTemp)

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        self.displayRaspiTemp = self._settings.get(["displayRaspiTemp"])

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
