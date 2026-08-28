# GNU Solfege - free ear training software
# Copyright (C) 2004, 2005, 2007, 2008, 2011, 2016 Tom Cato Amundsen
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


import os
import sys

from gi.repository import Gio, Gtk, GdkPixbuf


_ICON_SIZE_PIXELS = {
    Gtk.IconSize.MENU: 16,
    Gtk.IconSize.SMALL_TOOLBAR: 16,
    Gtk.IconSize.LARGE_TOOLBAR: 24,
    Gtk.IconSize.BUTTON: 16,
    Gtk.IconSize.DND: 32,
    Gtk.IconSize.DIALOG: 48,
}


class BaseIconFactory(object):
    """Load Solfege assets without GTK's deprecated stock icon API."""

    def __init__(self, widget, datadir):
        self.datadir = datadir
        self._icons = {}

    def add_icons(self, icons):
        for icon_id, filename in list(icons.items()):
            path = os.path.join(self.datadir, filename)
            if os.path.isfile(path):
                self._icons[icon_id] = path
            else:
                print("File not found: %s" % filename, file=sys.stderr)

    def get_pixbuf(self, icon_id, icon_size=Gtk.IconSize.DIALOG):
        size = _ICON_SIZE_PIXELS.get(icon_size, 48)
        return GdkPixbuf.Pixbuf.new_from_file_at_scale(
            self._icons[icon_id], size, size, True)

    def get_gicon(self, icon_id):
        return Gio.FileIcon.new(Gio.File.new_for_path(self._icons[icon_id]))

    def new_image(self, icon_id, icon_size=Gtk.IconSize.BUTTON):
        return Gtk.Image.new_from_pixbuf(self.get_pixbuf(icon_id, icon_size))


class EditorIconFactory(BaseIconFactory):
    """
    This class is used by lessonfile_editor.py
    """

    def __init__(self, widget, datadir):
        BaseIconFactory.__init__(self, widget, datadir)
        icons = {'solfege-icon': "graphics/solfege.svg",
            'solfege-sharp': "graphics/sharp.svg",
            'solfege-double-sharp': "graphics/double-sharp.svg",
            'solfege-flat': "graphics/flat.svg",
            'solfege-double-flat': "graphics/double-flat.svg",
            'solfege-natural': "graphics/natural.svg",
            'solfege-erase': "graphics/erase.svg",
            'solfege-notehead': "graphics/notehead.svg"}
        self.add_icons(icons)


class SolfegeIconFactory(BaseIconFactory):

    def __init__(self, widget, datadir):
        BaseIconFactory.__init__(self, widget, datadir)
        icon_list = [
            'rhythm-c12c12c12', 'rhythm-c12c12r12', 'rhythm-c12r12c12',
            'rhythm-c16c16c16c16', 'rhythm-c16c16c8', 'rhythm-c16c8c16',
            'rhythm-c16c8.', 'rhythm-c4', 'rhythm-c8c16c16', 'rhythm-c8.c16',
            'rhythm-c8c8', 'rhythm-r12c12c12', 'rhythm-r12c12r12',
            'rhythm-r12r12c12', 'rhythm-r16c16c16c16', 'rhythm-r16c16c8',
            'rhythm-r16c8c16', 'rhythm-r16c8.', 'rhythm-r4',
            'rhythm-r8c16c16', 'rhythm-r8c8', 'rhythm-r8r16c16',
            'rhythm-wrong']
        d = {}
        d['solfege-icon'] = 'graphics/solfege.svg'
        for iname in icon_list:
            if os.path.exists(os.path.join("graphics", iname) + ".svg"):
                d['solfege-%s' % iname] = os.path.join("graphics", iname) + ".svg"
            else:
                d['solfege-%s' % iname] = os.path.join("graphics", iname) + ".png"
        self.add_icons(d)
