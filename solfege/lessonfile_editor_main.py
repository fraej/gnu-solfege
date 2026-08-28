# -*- coding: iso-8859-1 -*-
# GNU Solfege - free ear training software
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2011, 2016  Tom Cato Amundsen
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from solfege import mpd
from solfege import gu
from solfege import lessonfile
from solfege import dataparser
from solfege import stock
from solfege.mpd import engravers, musicdisplayer

app_version = "0.1.4"


class HelpWindow(Gtk.Window):

    def __init__(self, parent):
        Gtk.Window.__init__(self)
        self.set_title(_("GNU Solfege lesson file editor"))
        self.set_default_size(400, 400)
        self.g_parent = parent
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.set_spacing(8)
        self.add(self.vbox)
        self.connect('delete_event', self.delete_cb)
        self.g_htmlwidget = Gtk.TextView(editable=False, cursor_visible=False,
                                         wrap_mode=Gtk.WrapMode.WORD)
        self.vbox.pack_start(self.g_htmlwidget, True, True, 0)
        self.vbox.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        bbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        bbox.set_border_width(8)
        self.vbox.pack_start(bbox, False, False, 0)
        b = Gtk.Button.new_with_mnemonic(_("_Close"))
        b.connect('clicked', self.close_cb)
        bbox.pack_start(b, True, True, 0)
        self.show_all()
        self.set_focus(b)

    def source(self, html):
        self.g_htmlwidget.get_buffer().set_text(html)

    def delete_cb(self, *v):
        self.g_parent.g_help_window = None

    def close_cb(self, w):
        self.g_parent.g_help_window = None
        self.destroy()


window_actions = [
    ('FileMenu', None, _('_File')),
    ('NewLessonfile', None, _('_New'), '<ctrl>N', 'new file', 'file_new_cb'),
    ('Open', None, _('_Open'), '<ctrl>O', 'Open lesson file', 'file_open_cb'),
    ('Save', None, _('_Save'), '<ctrl>S', 'Save the lesson file', 'file_save_cb'),
    ('SaveAs', None, _('Save _As…'), '<shift><ctrl>S', 'Save the lesson file with a new name', 'file_save_as_cb'),
    ('Quit', None, _('_Quit'), '<ctrl>Q', 'Quit program', 'quit_cb'),
    ('HelpMenu', None, _('_Help')),
    ('HelpHelp', None, _('_Help'), 'F1', None, 'help_cb'),
    ('HelpAbout', None, _('_About'), '', '', 'about_cb'),
]
lessonfile_actions = [
    ('GotoFirstQuestion', None, _('First question'), None,
     _('Go to the first question'), 'goto_first_question_cb'),
    ('GoBackQuestion', None, _('Previous question'), None,
     _('Go to the previous question'), 'go_back_question_cb'),
    ('GoForwardQuestion', None, _('Next question'), None,
     _('Go to the next question'), 'go_forward_question_cb'),
    ('GotoLastQuestion', None, _('Last question'), None,
     _('Go to the last question'), 'goto_last_question_cb'),
    ('NewQuestion', None, _('New question'), None,
     _('Add a new question'), 'new_question_cb'),
    ('NoteheadCursor', None, _("Noteheads"), None,
     _('Add noteheads'), 'select_cursor_notehead_cb'),
    ('SharpCursor', None, _("Sharps"), None,
     _('Add sharps'), 'select_cursor_sharp_cb'),
    ('DoubleSharpCursor', None, _("Double sharps"), None,
     _('Add double-sharps'), 'select_cursor_2sharp_cb'),
    ('NaturalCursor', None, _("Naturals"), None,
     _('Remove accidentals'), 'select_cursor_natural_cb'),
    ('FlatCursor', None, _("Flats"), None,
     _('Add flats'), 'select_cursor_flat_cb'),
    ('DoubleFlatCursor', None, _("Double flats"), None,
     _('Add double-flats'), 'select_cursor_2flat_cb'),
    ('EraseCursor', None, _("Erase"), None,
     _('Delete tones'), 'select_cursor_erase_cb'),
]
ui_string = """<ui>
  <menubar name='Menubar'>
    <menu action='FileMenu'>
      <menuitem action='NewLessonfile'/>
      <menuitem action='Open'/>
      <menuitem action='Save'/>
      <menuitem action='SaveAs'/>
      <separator/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='HelpHelp'/>
      <menuitem action='HelpAbout'/>
    </menu>
  </menubar>
  <toolbar name='Toolbar'>
    <toolitem action='GotoFirstQuestion'/>
    <toolitem action='GoBackQuestion'/>
    <toolitem action='GoForwardQuestion'/>
    <toolitem action='GotoLastQuestion'/>
    <toolitem action='NewQuestion'/>
    <separator/>
    <toolitem action='NoteheadCursor'/>
    <toolitem action='DoubleSharpCursor'/>
    <toolitem action='SharpCursor'/>
    <toolitem action='NaturalCursor'/>
    <toolitem action='FlatCursor'/>
    <toolitem action='DoubleFlatCursor'/>
    <toolitem action='EraseCursor'/>
  </toolbar>
</ui>"""


def fix_actions(actions, instance):
    "Helper function to map methods to an instance"
    retval = []
    for i in range(len(actions)):
        curr = actions[i]
        if len(curr) > 5:
            curr = list(curr)
            curr[5] = getattr(instance, curr[5])
            curr = tuple(curr)
        retval.append(curr)
    return retval


class EditorLessonfile(object):

    def __init__(self):
        self.m_filename = None
        self.m_changed = False
        self.header = lessonfile._Header({'module': 'chord'})
        self.m_questions = [dataparser.Question()]
        self.m_questions[-1].music = lessonfile.Music("")
        self.m_questions[-1].name = ""
        self._idx = 0


class MainWin(Gtk.ApplicationWindow):

    def __init__(self, application, datadir):
        Gtk.ApplicationWindow.__init__(self, application=application)
        self.icons = stock.EditorIconFactory(self, datadir)
        self.g_help_window = None
        # toplevel_vbox:
        #   -menubar
        #   -toolbar
        #   -notebook
        #   -statusbar
        self.toplevel_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.toplevel_vbox)
        self.create_menu_and_toolbar()
        self.g_notebook = Gtk.Notebook()
        self.toplevel_vbox.pack_start(self.g_notebook, True, True, 0)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toplevel_vbox.pack_start(self.vbox, True, True, 0)
        self.create_mainwin_ui()
        self.show_all()

    def create_mainwin_ui(self):
        qbox = gu.hig_dlg_vbox()
        self.g_notebook.append_page(qbox, Gtk.Label(label=_("Questions")))
        gu.bLabel(qbox, _("Enter new chords using the mouse"), False, False)
        hbox = gu.bHBox(qbox, False, False)
        self.g_displayer = musicdisplayer.ChordEditor()
        self.g_displayer.connect('clicked', self.on_displayer_clicked)
        self.g_displayer.clear(2)
        gu.bLabel(hbox, "")
        hbox.pack_start(self.g_displayer, False, False, 0)
        gu.bLabel(hbox, "")
        ##
        self.g_question_name = Gtk.Entry()
        qbox.pack_start(
            gu.hig_label_widget(_("Question title:"), self.g_question_name, None),
            False, False, 0)
        self.g_navinfo = Gtk.Label(label="")
        qbox.pack_start(self.g_navinfo, False, False, 0)

        ##
        self.m_P = EditorLessonfile()
        cvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.g_notebook.append_page(cvbox, Gtk.Label(label=_("Lessonfile header")))
        # Header section
        sizegroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        self.g_title = Gtk.Entry()
        cvbox.pack_start(
            gu.hig_label_widget(_("File title:"), self.g_title, sizegroup),
            True, True, 0)
        self.g_content_chord = Gtk.RadioButton.new_with_label(None, "chord")
        self.g_content_chord_voicing = Gtk.RadioButton.new_with_label_from_widget(
            self.g_content_chord, "chord-voicing")
        self.g_content_idbyname = Gtk.RadioButton.new_with_label_from_widget(
            self.g_content_chord, "id-by-name")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.g_content_chord, True, True, 0)
        box.pack_start(self.g_content_chord_voicing, True, True, 0)
        box.pack_start(self.g_content_idbyname, True, True, 0)
        cvbox.pack_start(
            gu.hig_label_widget(_("Content:"), box, sizegroup), True, True, 0)
        self.g_random_transpose = Gtk.Entry()
        cvbox.pack_start(
            gu.hig_label_widget(
                _("Random transpose:"), self.g_random_transpose, sizegroup),
            True, True, 0)
        #
        #self.g_statusbar = Gtk.Statusbar()
        #self.toplevel_vbox.pack_start(self.g_statusbar, False)
        self.update_appwin()

    def proceed_if_changed(self):
        if not self.m_P.m_changed:
            return True
        dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION,
              Gtk.ButtonsType.YES_NO, _("You have unsaved data. Proceed anyway?"))
        dialog.hide()
        if dialog.run() == Gtk.ResponseType.YES:
            dialog.destroy()
            return True
        dialog.destroy()
        return False

    def update_appwin(self):
        self.update_score()
        self.set_navinfo()
        self.g_title.set_text(self.m_P.header.title)
        self.g_random_transpose.set_text(str(self.m_P.header.random_transpose))
        {'chord': self.g_content_chord,
         'chordvoicing': self.g_content_chord_voicing,
         'idbyname': self.g_content_idbyname}[self.m_P.header.module].set_active(True)

    def set_navinfo(self):
        if self.m_P.m_filename:
            self.set_title(self.m_P.m_filename)
        else:
            self.set_title(_("No file"))
        self.g_navinfo.set_text(_("question %(idx)i of %(count)i") % {
            'idx': self.m_P._idx + 1,
            'count': len(self.m_P.m_questions)})
        self.g_question_name.set_text(self.m_P.m_questions[self.m_P._idx].name)

    def load_file(self, filename):
        self.m_P = lessonfile.ChordLessonfile(filename)
        self.m_P.m_changed = False
        if self.m_P.m_questions:
            self.m_P._idx = 0
            self.set_navinfo()
        else:
            # Do a little trick to make an empty question
            self.m_P.m_questions = [dataparser.Question()]
            self.m_P.m_questions[-1].music = lessonfile.Music("")
            self.m_P.m_questions[-1].name = ""
            self.m_P._idx = 0

        if self.m_P.header.module not in ('idbyname', 'chord', 'chordvoicing'):
                dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE,
                    _("The exercise module '%s' is not supported yet. Cannot edit this file.") % c)
                dialog.run()
                dialog.destroy()
                self.m_P = EditorLessonfile()
        self.update_appwin()

    def file_open_cb(self, *v):
        dialog = Gtk.FileChooserDialog(
            title=_("Open..."), transient_for=self,
            action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                           _("_Open"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self.load_file(filename)
            except Exception as e:
                dialog.destroy()
                m = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.CLOSE,
                        _("Loading file '%(filename)s' failed: %(msg)s") %
                            {'filename': filename, 'msg': e})
                m.run()
                m.destroy()
            else:
                dialog.destroy()
        else:
            dialog.destroy()

    def file_new_cb(self, action, v=None):
        if self.proceed_if_changed():
            self.m_P = EditorLessonfile()
            self.update_appwin()

    def file_save_as_cb(self, *v):
        self.store_data_from_ui()
        dialog = Gtk.FileChooserDialog(
            title=_("Save as..."), transient_for=self,
            action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                           _("_Save"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            self.m_P.m_filename = dialog.get_filename()
            self.save_file()
        dialog.destroy()

    def file_save_cb(self, *v):
        self.store_data_from_ui()
        if self.m_P.m_filename is None:
            dialog = Gtk.FileChooserDialog(
                title=_("Save..."), transient_for=self,
                action=Gtk.FileChooserAction.SAVE)
            dialog.add_buttons(_("_Cancel"), Gtk.ResponseType.CANCEL,
                               _("_Save"), Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)

            if dialog.run() == Gtk.ResponseType.OK:
                self.m_P.m_filename = dialog.get_filename()
            dialog.destroy()
        if self.m_P.m_filename:
            self.update_appwin()
            self.save_file()

    def save_file(self):
        if not self.m_P.m_filename:
            raise Exception("No filename. Cannot save.")
        ofile = open(self.m_P.m_filename, 'w')
        ofile.write("# Creator: GNU Solfege lesson file editor %s\n\n"
                    % app_version)
        ofile.write("header {\n    module = %s\n" % self.m_P.header.module)
        if type(self.m_P.header.random_transpose) == list:
            ofile.write("    random_transpose = %s, %s, %s\n" % (self.m_P.header.random_transpose[0],
                            self.m_P.header.random_transpose[1], self.m_P.header.random_transpose[2]))
        else:
            ofile.write("    random_transpose = yes\n")
        if self.m_P.header.lesson_id:
            ofile.write('    lesson_id = "%s"\n' % self.m_P.header.lesson_id)
        ofile.write('    title = "%s"\n}\n' % self.m_P.header.title)
        for q in self.m_P.m_questions:
            print('question {', file=ofile)
            print('    name = "%s"' % q.name, file=ofile)
            print('    music = music("%s", chord)' % q.music.m_musicdata, file=ofile)
            print('}', file=ofile)
        ofile.close()
        self.m_P.m_changed = False

    def quit_cb(self, *v):
        if self.proceed_if_changed():
            self.get_application().quit()

    def help_cb(self, *v):
        if not self.g_help_window:
            self.g_help_window = HelpWindow(self)
            self.g_help_window.source("""<html>
<body>
<h2>GNU Solfege lesson file editor %s</h2>
<p>This is the very first unfinished release. Backup the files you
edit, since it can screw up.</p>
<p>The parser can create files for the chord exercise. It can parse more
advanced lesson files than it can write. So you might loose data if you
edit your hand written lesson files with this program.</p>
</body>
</html>
""" % app_version)
            self.g_help_window.show()
        else:
            self.g_help_window.present()

    def about_cb(self, *v):
        dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO,
            Gtk.ButtonsType.CLOSE, "GNU Solfege lesson file editor %s\nCopyright (C) 2004, 2005 Tom Cato Amundsen <tca@gnu.org>" % app_version)
        dialog.run()
        dialog.destroy()

    def goto_first_question_cb(self, *v):
        self.store_data_from_ui()
        self.m_P._idx = 0
        self.update_appwin()

    def go_back_question_cb(self, *v):
        self.store_data_from_ui()
        self.m_P._idx = max(0, self.m_P._idx - 1)
        self.update_appwin()

    def go_forward_question_cb(self, *v):
        self.store_data_from_ui()
        self.m_P._idx = min(self.m_P._idx + 1, len(self.m_P.m_questions) - 1)
        self.update_appwin()

    def goto_last_question_cb(self, *v):
        self.store_data_from_ui()
        self.m_P._idx = len(self.m_P.m_questions) - 1
        self.update_appwin()

    def new_question_cb(self, *v):
        self.store_data_from_ui()
        self.m_P.m_questions.append(dataparser.Question())
        self.m_P.m_questions[-1].music = lessonfile.Music("")
        self.m_P.m_questions[-1].name = ""
        self.m_P._idx = len(self.m_P.m_questions) - 1
        self.update_appwin()

    def select_cursor_2flat_cb(self, *v):
        self.g_displayer.set_cursor("-2")

    def select_cursor_flat_cb(self, *v):
        self.g_displayer.set_cursor(-1)

    def select_cursor_natural_cb(self, *v):
        self.g_displayer.set_cursor(0)

    def select_cursor_sharp_cb(self, *v):
        self.g_displayer.set_cursor("1")

    def select_cursor_2sharp_cb(self, *v):
        self.g_displayer.set_cursor("2")

    def select_cursor_erase_cb(self, *v):
        self.g_displayer.set_cursor("erase")

    def select_cursor_notehead_cb(self, *v):
        self.g_displayer.set_cursor("notehead")

    def update_score(self):
        """
        Set m_chord_tones based on the data in the lesson file.
        Then call g_displayer.display to show the music.
        """
        assert self.m_P
        self.m_chord_tones = {}
        for n in self.m_P.m_questions[self.m_P._idx].music.m_musicdata.split():
            p = mpd.MusicalPitch.new_from_notename(n)
            self.m_chord_tones[p.steps()] = p
        #
        if self.m_chord_tones:
            s = ""
            for n in list(self.m_chord_tones.values()):
                s += " " + n.get_octave_notename()
            self.g_displayer.display("\\staff{ < %s >}\\staff{\\clef bass}" % s, 20)
        else:
            self.g_displayer.display("\\staff{ }\\staff{\\clef bass}", 20)
        self.g_displayer.set_size_request(400, -1)

    def store_data_from_ui(self):
        self.m_P.m_questions[self.m_P._idx].name = self.g_question_name.get_text()
        self.m_P.header.title = self.g_title.get_text()
        self.m_P.header.random_transpose = eval(self.g_random_transpose.get_text())
        if self.g_content_chord.get_active():
            self.m_P.header.module = 'chord'
        if self.g_content_chord_voicing.get_active():
            self.m_P.header.module = 'chordvoicing'
        if self.g_content_idbyname.get_active():
            self.m_P.header.module = 'idbyname'

    def on_displayer_clicked(self, ed, steps):
        self.m_P.m_changed = True
        notename = ("c", "d", "e", "f", "g", "a", "b")[6 - (steps % 7)]
        n = mpd.MusicalPitch.new_from_notename(notename)
        n.m_octave_i = 1 - (steps // 7)
        if self.g_displayer.m_cursor == 'notehead':
            if n.steps() not in self.m_chord_tones:
                self.m_chord_tones[n.steps()] = n
        elif self.g_displayer.m_cursor == 'erase':
            if n.steps() in self.m_chord_tones:
                del self.m_chord_tones[n.steps()]
        else:
            if n.steps() not in self.m_chord_tones:
                return
            else:
                self.m_chord_tones[n.steps()].m_accidental_i = int(self.g_displayer.m_cursor)
        v = list(self.m_chord_tones.values())
        v.sort()
        v = [y.get_octave_notename() for y in v]
        self.m_P.m_questions[self.m_P._idx].music.m_musicdata = " ".join(v)
        self.update_score()


class EditorMainWin(MainWin):

    def __init__(self, application, datadir):
        MainWin.__init__(self, application, datadir)

    def create_menu_and_toolbar(self):
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        menubar = Gtk.MenuBar()
        file_item = Gtk.MenuItem.new_with_mnemonic(_('_File'))
        file_menu = Gtk.Menu()
        file_item.set_submenu(file_menu)
        menubar.append(file_item)
        for label, accelerator, callback in (
                (_('_New'), '<ctrl>N', self.file_new_cb),
                (_('_Open'), '<ctrl>O', self.file_open_cb),
                (_('_Save'), '<ctrl>S', self.file_save_cb),
                (_('Save _As…'), '<shift><ctrl>S', self.file_save_as_cb)):
            self._add_menu_item(file_menu, label, callback, accelerator,
                                accel_group)
        file_menu.append(Gtk.SeparatorMenuItem())
        self._add_menu_item(file_menu, _('_Quit'), self.quit_cb, '<ctrl>Q',
                            accel_group)

        help_item = Gtk.MenuItem.new_with_mnemonic(_('_Help'))
        help_menu = Gtk.Menu()
        help_item.set_submenu(help_menu)
        menubar.append(help_item)
        self._add_menu_item(help_menu, _('_Help'), self.help_cb, 'F1',
                            accel_group)
        self._add_menu_item(help_menu, _('_About'), self.about_cb, None,
                            accel_group)
        self.toplevel_vbox.pack_start(menubar, False, False, 0)

        toolbar = Gtk.Toolbar()
        toolbar.set_show_arrow(False)
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        for label, icon_name, callback in (
                (_('First question'), 'go-first-symbolic',
                 self.goto_first_question_cb),
                (_('Previous question'), 'go-previous-symbolic',
                 self.go_back_question_cb),
                (_('Next question'), 'go-next-symbolic',
                 self.go_forward_question_cb),
                (_('Last question'), 'go-last-symbolic',
                 self.goto_last_question_cb),
                (_('New question'), 'list-add-symbolic',
                 self.new_question_cb)):
            image = Gtk.Image.new_from_icon_name(
                icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            button = Gtk.ToolButton.new(image, label)
            button.set_tooltip_text(label)
            button.connect('clicked', callback)
            toolbar.insert(button, -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        for label, icon_id, callback in (
                (_('Add noteheads'), 'solfege-notehead',
                 self.select_cursor_notehead_cb),
                (_('Add double-sharps'), 'solfege-double-sharp',
                 self.select_cursor_2sharp_cb),
                (_('Add sharps'), 'solfege-sharp',
                 self.select_cursor_sharp_cb),
                (_('Remove accidentals'), 'solfege-natural',
                 self.select_cursor_natural_cb),
                (_('Add flats'), 'solfege-flat',
                 self.select_cursor_flat_cb),
                (_('Add double-flats'), 'solfege-double-flat',
                 self.select_cursor_2flat_cb),
                (_('Delete tones'), 'solfege-erase',
                 self.select_cursor_erase_cb)):
            button = Gtk.ToolButton.new(
                self.icons.new_image(icon_id, Gtk.IconSize.LARGE_TOOLBAR),
                label)
            button.set_tooltip_text(label)
            button.connect('clicked', callback)
            toolbar.insert(button, -1)
        self.toplevel_vbox.pack_start(toolbar, False, False, 0)

    @staticmethod
    def _add_menu_item(menu, label, callback, accelerator, accel_group):
        item = Gtk.MenuItem.new_with_mnemonic(label)
        item.connect('activate', callback)
        if accelerator:
            key, modifiers = Gtk.accelerator_parse(accelerator)
            item.add_accelerator('activate', accel_group, key, modifiers,
                                 Gtk.AccelFlags.VISIBLE)
        menu.append(item)


def main(datadir):
    engravers.fetadir = os.path.join(datadir, "feta")
    application = Gtk.Application(
        application_id="org.gnu.solfege.LessonfileEditor")

    def activate(app):
        if app.get_active_window():
            app.get_active_window().present()
            return
        window = EditorMainWin(app, datadir)
        if len(sys.argv) == 2:
            window.load_file(sys.argv[1])
        window.show()

    application.connect('activate', activate)
    return application.run([sys.argv[0]])
