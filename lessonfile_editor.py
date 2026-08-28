#!/usr/bin/python3
# GNU Solfege - free ear training software
# Copyright (C) 2004, 2005, 2006, 2011, 2016  Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
TODO/BUGS
=========

The program only runs from sourcedir. It cannot be installed.

If you open a file that includes other files, the questions from all
files will be edited as a single file, and when you save, the include
statement will be missing, and all questions are saved in one file.
The included files are un-touched.

"""

import os
import sys

datadir = os.path.dirname(os.path.abspath(__file__))
os.chdir(datadir)
sys.path.insert(0, datadir)

from solfege import cfg, filesystem, i18n, presetup

presetup.presetup(os.path.join(datadir, "default.config"), None,
                  filesystem.rcfile())
i18n.setup(datadir, cfg.get_string("app/lc_messages"))

from solfege import lessonfile_editor_main

sys.exit(lessonfile_editor_main.main(datadir))
