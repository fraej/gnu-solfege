# vim: set fileencoding=utf-8 :
# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2011, 2016  Tom Cato Amundsen
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


import solfege


import webbrowser
import textwrap
# We move x-www-browser to the end of the list because on my
# debian etch system, the browser does will freeze solfege until
# I close the browser window.
try:
    webbrowser.get()
    i = webbrowser._tryorder.index("x-www-browser")
    webbrowser._tryorder.append(webbrowser._tryorder[i])
    del webbrowser._tryorder[i]
except (ValueError, webbrowser.Error):
    pass

import sys
import traceback
import locale
import os
import shutil

try:
    from pyalsa import alsaseq
except ImportError:
    alsaseq = None

from solfege import winlang
from solfege import buildinfo
from solfege.esel import FrontPage, TestsView, SearchView, UserView

from gi.repository import Gtk
from gi.repository import Gdk

from solfege import i18n


class SplashWin(Gtk.Window):

    def __init__(self, gtk_application):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        gtk_application.add_window(self)
        self.set_decorated(False)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        self.add(frame)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(20)
        frame.add(vbox)
        l = Gtk.Label(label=_("Starting GNU Solfege %s") % buildinfo.VERSION_STRING)
        l.set_name("Heading1")
        vbox.pack_start(l, True, True, 0)
        self.g_infolabel = Gtk.Label(label='')
        vbox.pack_start(self.g_infolabel, True, True, 0)
        self.show_all()

    def show_progress(self, txt):
        self.g_infolabel.set_text(txt)
        while Gtk.events_pending():
            Gtk.main_iteration()

from solfege.configwindow import ConfigWindow
from solfege.profilemanager import ChangeProfileDialog, ProfileManager
from solfege import gu
from solfege import cfg
from solfege import mpd
from solfege import lessonfile
from solfege import download_pyalsa
from solfege import statistics
from solfege import stock


from solfege import frontpage
from solfege import fpeditor
from solfege.trainingsetdlg import TrainingSetDialog
from solfege.practisesheetdlg import PractiseSheetDialog
from solfege import filesystem


class MusicViewerWindow(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, transient_for=parent)
        self.set_default_size(500, 300)
        self.g_music_displayer = mpd.MusicDisplayer()
        self.vbox.pack_start(self.g_music_displayer, True, True, 0)
        b = gu.bButton(self.action_area, _("Close"), solfege.win.close_musicviewer)
        b.grab_focus()
        self.connect('destroy', solfege.win.close_musicviewer)
        self.show_all()

    def display_music(self, music):
        fontsize = cfg.get_int('config/feta_font_size=20')
        self.g_music_displayer.display(music, fontsize)


class MainWin(Gtk.ApplicationWindow, cfg.ConfigUtils):
    default_front_page = os.path.join(lessonfile.exercises_dir, 'learningtree.txt')
    debug_front_page = os.path.join(lessonfile.exercises_dir, 'debugtree.txt')

    def __init__(self, gtk_application, options, datadir):
        Gtk.ApplicationWindow.__init__(self, application=gtk_application)
        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._vbox.show()
        self.add(self._vbox)
        self.icons = stock.SolfegeIconFactory(self, datadir)
        cfg.ConfigUtils.__dict__['__init__'](self, 'mainwin')
        self.set_resizable(self.get_bool('gui/mainwin_user_resizeable'))
        self.add_watch('gui/mainwin_user_resizeable', lambda s: self.set_resizable(self.get_bool('gui/mainwin_user_resizeable')))
        self.connect('delete-event', self.quit_program)
        self.connect('key_press_event', self.on_key_press_event)
        self.g_about_window = None
        self.m_exercise = None
        self.m_viewer = None
        self.box_dict = {}
        self.g_config_window = None
        self.g_path_info_dlg = None
        self.g_musicviewer_window = None
        self.m_history = []
        self._not_exit_widgets = []
        self.setup_menu()
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.show()
        self._vbox.pack_start(self.main_box, True, True, 0)

    def get_view(self):
        """
        Return the view that is currently visible.
        Raise KeyError if no view has yet been added.
        """
        return self.box_dict[self.m_viewer]

    def add_view(self, view, name):
        """
        Hide the current view.
        Add and view the new view.
        """
        assert name not in self.box_dict
        if self.m_viewer:
            self.get_view().hide()
        self.box_dict[name] = view
        self.main_box.pack_start(self.box_dict[name], True, True, 0)
        self.box_dict[name].show()
        self.m_viewer = name

    def show_view(self, name):
        """
        Return False if the view does not exist.
        Hide the current visible view, show the view named 'name' and
        return True.
        """
        if name not in self.box_dict:
            return False
        self.get_view().hide()
        self.m_viewer = name
        self.box_dict[name].show()
        return True

    def change_frontpage(self, filename):
        """
        Change to a different frontpage file.
        """
        self.set_string('app/frontpage', filename)
        self.load_frontpage()

    def load_frontpage(self):
        """
        Load the front page file set in the config database into
        solfege.app.m_frontpage_data
        """
        filename = self.get_string("app/frontpage")
        if filename == self.debug_front_page and not solfege.app.m_options.debug:
            self.set_string("app/frontpage", self.default_front_page)
            filename = self.default_front_page
        if not os.path.isfile(filename):
            filename = self.default_front_page
        try:
            solfege.app.m_frontpage_data = frontpage.load_tree(filename)
        except Exception:
            if solfege.splash_win:
                solfege.splash_win.hide()
            solfege.app.m_frontpage_data = frontpage.load_tree(self.default_front_page)
            self.set_string('app/frontpage', self.default_front_page)
            gu.dialog_ok(_("Loading front page '%s' failed. Using default page." % filename),
                parent=self,
                secondary_text="\n".join(traceback.format_exception(*sys.exc_info())))
            if solfege.splash_win:
                solfege.splash_win.show()
        self.display_frontpage()

    def setup_menu(self):
        self._accel_group = Gtk.AccelGroup()
        self.add_accel_group(self._accel_group)
        menubar = Gtk.MenuBar()
        self._vbox.pack_start(menubar, False, False, 0)

        file_root, file_menu = self._add_submenu(menubar, _('_File'))
        self._add_menu_item(file_menu, _('_Front Page'),
                            lambda w: self.display_frontpage(), 'F5')
        self._add_menu_item(file_menu, _('_Tests Page'),
                            lambda w: self.display_testpage(), 'F6')
        self._add_menu_item(file_menu, _('_Recent Exercises'),
                            self.display_recent_exercises, 'F7')
        self._add_menu_item(file_menu, _('_Recent Tests'),
                            self.display_recent_tests, 'F8')
        self._add_menu_item(file_menu, _('_User Exercises'),
                            self.display_user_exercises, 'F9')
        self._add_menu_item(file_menu, _('_Search Exercises'),
                            self.on_search_all_exercises, '<ctrl>F')
        file_menu.append(Gtk.SeparatorMenuItem())
        self.g_frontpages_item, self.g_frontpages_menu = self._add_submenu(
            file_menu, _('Sele_ct Front Page'))
        self._not_exit_widgets.append(self.g_frontpages_item)
        self.g_frontpages_item.connect(
            'activate', lambda item: self.create_frontpage_menu())
        file_menu.append(Gtk.SeparatorMenuItem())
        self._add_menu_item(file_menu, _('_Edit Front Page'),
                            self.do_tree_editor)
        self._add_menu_item(file_menu,
                            _('E_xport Exercises to Audio Files…'),
                            self.new_training_set_editor)
        self._add_menu_item(file_menu, _('Ear Training Test Pri_ntout…'),
                            self.new_practisesheet_editor)
        file_menu.append(Gtk.SeparatorMenuItem())
        self._add_menu_item(file_menu, _("Profile _Manager"),
                            self.open_profile_manager)
        self._add_menu_item(file_menu, _('_Preferences'),
                            self.open_preferences_window, '<ctrl>F12')
        self._add_menu_item(file_menu, _('_Quit'), self.quit_program,
                            '<ctrl>Q', disable_in_test=False)

        self.g_help_root, help_menu = self._add_submenu(menubar, _('_Help'))
        self._not_exit_widgets.append(self.g_help_root)
        self._add_menu_item(help_menu, _('_User manual'),
                            lambda o: solfege.app.handle_href('index.html'))
        self.g_help_current_item = self._add_menu_item(
            help_menu, _('_Help on the current exercise'),
            lambda o: solfege.app.please_help_me(), 'F1')
        self.g_help_theory_item = self._add_menu_item(
            help_menu, _('_Music theory on the current exercise'),
            lambda o: solfege.app.show_exercise_theory(), 'F3')
        self.g_help_current_item.hide()
        self.g_help_theory_item.hide()
        self._add_menu_item(help_menu, _('_File locations'),
                            self.show_path_info)
        theory_root, theory_menu = self._add_submenu(help_menu, _('The_ory'))
        self._not_exit_widgets.append(theory_root)
        self._add_menu_item(theory_menu, _('_Intervals'),
                            lambda o: solfege.app.handle_href(
                                'theory-intervals.html'))
        self.g_setup_pyalsa_item = self._add_menu_item(
            help_menu, _("Download and compile ALSA modules"),
            self.setup_pyalsa)
        if sys.platform != 'linux':
            self.g_setup_pyalsa_item.hide()
        help_menu.append(Gtk.SeparatorMenuItem())
        self._add_menu_item(help_menu, _('_Mailing lists, web page etc.'),
                            lambda o: solfege.app.handle_href(
                                'online-resources.html'))
        self._add_menu_item(help_menu, _('Reporting _bugs'),
                            lambda o: solfege.app.handle_href(
                                'bug-reporting.html'))
        self._add_menu_item(help_menu, _('_About'), self.show_about_window)
        menubar.show_all()
        self.g_help_current_item.hide()
        self.g_help_theory_item.hide()
        if sys.platform != 'linux':
            self.g_setup_pyalsa_item.hide()

    def _add_submenu(self, parent, label):
        item = Gtk.MenuItem.new_with_mnemonic(label)
        menu = Gtk.Menu()
        item.set_submenu(menu)
        parent.append(item)
        return item, menu

    def _add_menu_item(self, menu, label, callback, accelerator=None,
                       disable_in_test=True):
        item = Gtk.MenuItem.new_with_mnemonic(label)
        item.connect('activate', callback)
        if accelerator:
            key, modifiers = Gtk.accelerator_parse(accelerator)
            item.add_accelerator('activate', self._accel_group, key, modifiers,
                                 Gtk.AccelFlags.VISIBLE)
        menu.append(item)
        if disable_in_test:
            self._not_exit_widgets.append(item)
        return item

    def create_frontpage_menu(self):
        """
        Create, or update if already existing, the submenu that let the
        user choose which front page file to display.
        """
        for child in self.g_frontpages_menu.get_children():
            self.g_frontpages_menu.remove(child)
        old_dir = None
        for fn in frontpage.get_front_pages_list(solfege.app.m_options.debug):
            if solfege.splash_win:
                solfege.splash_win.show_progress(fn)
            if not frontpage.may_be_frontpage(fn):
                continue
            try:
                lessonfile.infocache.frontpage.get(fn, 'title')
            except TypeError:
                continue
            cur_dir = os.path.split(fn)[0]
            if old_dir != cur_dir:
                if old_dir is not None:
                    self.g_frontpages_menu.append(Gtk.SeparatorMenuItem())
                old_dir = cur_dir
            item = self._add_menu_item(
                self.g_frontpages_menu,
                lessonfile.infocache.frontpage.get(fn, 'title'),
                lambda o, filename=fn: self.change_frontpage(filename),
                disable_in_test=False)
            item.set_tooltip_text(fn)
        self.g_frontpages_menu.show_all()

    def show_help_on_current(self):
        """
        Show the menu entries for the exercise help and music theory
        pages on the Help menu.
        """
        self.g_help_current_item.show()
        self.g_help_theory_item.show()

    def hide_help_on_current(self):
        """
        Hide the menu entries for the help and music theory pages on the
        Help menu.
        """
        self.g_help_current_item.hide()
        self.g_help_theory_item.hide()

    def display_error_message2(self, text, secondary_text):
        """
        This is the new version of display_error_message, and it will
        eventually replace the old.
        """
        if solfege.splash_win and solfege.splash_win.props.visible:
            solfege.splash_win.hide()
            reshow_splash = True
        else:
            reshow_splash = False
        if not isinstance(text, str):
            text = text.decode(locale.getpreferredencoding(), 'replace')
        if not isinstance(secondary_text, str):
            secondary_text = secondary_text.decode(locale.getpreferredencoding(), 'replace')
        m = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                              Gtk.ButtonsType.CLOSE, text)
        if secondary_text:
            m.format_secondary_text(secondary_text)
        m.run()
        m.destroy()
        if reshow_splash:
            solfege.splash_win.show()
            while Gtk.events_pending():
                Gtk.main_iteration()

    def display_error_message(self, msg, title=None, secondary_text=None):
        if solfege.splash_win and solfege.splash_win.props.visible:
            solfege.splash_win.hide()
            reshow_splash = True
        else:
            reshow_splash = False
        if not isinstance(msg, str):
            msg = msg.decode(locale.getpreferredencoding(), 'replace')
        m = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                              Gtk.ButtonsType.CLOSE, None)
        m.set_markup(gu.escape(msg))
        if title:
            m.set_title(title)
        if secondary_text:
            m.format_secondary_text(secondary_text)
        m.run()
        m.destroy()
        if reshow_splash:
            solfege.splash_win.show()
            while Gtk.events_pending():
                Gtk.main_iteration()

    def show_path_info(self, w):
        if not self.g_path_info_dlg:
            self.g_path_info_dlg = Gtk.Dialog(
                title=_("_File locations").replace("_", ""),
                transient_for=self)
            self.g_path_info_dlg.add_button(_("_OK"),
                                             Gtk.ResponseType.ACCEPT)
            sc = Gtk.ScrolledWindow()
            sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            self.g_path_info_dlg.get_content_area().pack_start(
                sc, True, True, 0)
            #
            vbox = gu.hig_dlg_vbox()
            sc.add(vbox)

            box1, box2 = gu.hig_category_vbox(_("_File locations").replace("_", ""))
            vbox.pack_start(box1, True, True, 0)
            sizegroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
            # statistics.sqlite
            # win32 solfegerc
            # win32 langenviron.txt
            box2.pack_start(gu.hig_label_widget(_("Solfege application data:"), Gtk.Label(label=filesystem.app_data()), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget(_("Solfege user data:"), Gtk.Label(label=filesystem.user_data()), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget(_("Solfege config file:"), Gtk.Label(label=filesystem.rcfile()), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget(_("Solfege installation directory:"), Gtk.Label(label=os.getcwd()), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget(_("User manual in HTML format:"), Gtk.Label(label=os.path.join(os.getcwd(), "help")), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget("gtk:", Gtk.Label(label=str(Gtk)), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget("pyalsa:", Gtk.Label(label=str(alsaseq)), sizegroup), False, False, 0)
            box2.pack_start(gu.hig_label_widget(
                "PYTHONHOME",
                Gtk.Label(label=os.environ.get('PYTHONHOME', 'Not defined')),
                sizegroup), False, False, 0)
            self.g_path_info_dlg.show_all()

            def f(*w):
                self.g_path_info_dlg.hide()
                return True
            self.g_path_info_dlg.connect('response', f)
            self.g_path_info_dlg.connect('delete-event', f)
            unused, natural_size = vbox.get_preferred_size()
            geometry = gu.get_monitor_geometry(self)
            sc.set_size_request(
                int(min(natural_size.width + gu.hig.SPACE_LARGE * 2,
                        geometry.width * 0.9)),
                natural_size.height)

    def setup_pyalsa(self, widget):
        download_pyalsa.download()

    def show_about_window(self, widget):
        pixbuf = self.icons.get_pixbuf('solfege-icon', Gtk.IconSize.DIALOG)
        a = self.g_about_window = Gtk.AboutDialog()
        a.set_transient_for(self)
        a.set_program_name("GNU Solfege")
        a.set_logo(pixbuf)
        a.set_website("https://savannah.gnu.org/projects/solfege")
        a.set_version(buildinfo.VERSION_STRING)
        a.set_copyright("Copyright (C) 2013 Tom Cato Amundsen and others")
        a.set_license("\n".join((solfege.application.solfege_copyright, solfege.application.warranty)))
        # Using set_license_type causes the app to print warnings.
        # a.set_license_type(Gtk.License.GPL_3_0)
        a.set_authors(["Tom Cato Amundsen",
              'Giovanni Chierico %s' % _("(some lessonfiles)"),
              'Michael Becker %s' % _("(some lessonfiles)"),
              'Joe Lee %s' % _("(sound code for the MS Windows port)"),
              'Steve Lee %s' % _("(ported winmidi.c to gcc)"),
              'Thibaus Cousin %s' % _("(spec file for SuSE 8.2)"),
              'David Coe %s' % _("(spec file cleanup)"),
              'David Petrou %s' % _("(testing and portability fixes for FreeBSD)"),
              'Han-Wen Nienhuys %s' % _("(the music font from Lilypond)"),
              'Jan Nieuwenhuizen %s' % _("(the music font from Lilypond)"),
              'Davide Bonetti %s' % _("(scale exercises)"),
              ])
        a.set_documenters(["Tom Cato Amundsen",
                "Tom Eykens",
                ])
        if _("SOLFEGETRANSLATORS") == 'SOLFEGETRANSLATORS':
            a.set_translator_credits(None)
        else:
            a.set_translator_credits(_("SOLFEGETRANSLATORS"))
        self.g_about_window.run()
        self.g_about_window.destroy()

    def do_tree_editor(self, *v):
        """
        Open a front page editor editing the current front page.
        """
        fpeditor.Editor.edit_file(self.get_string("app/frontpage"))

    def post_constructor(self):
        self.create_frontpage_menu()
        if solfege.app.m_sound_init_exception is not None:
            if solfege.splash_win:
                solfege.splash_win.destroy()
                solfege.splash_win = None
            solfege.app.display_sound_init_error_message(solfege.app.m_sound_init_exception)
        try:
            i18n.locale_setup_failed
            print("\n".join(textwrap.wrap("Translations are disabled because your locale settings are broken. This is not a bug in GNU Solfege, so don't report it. The README file distributed with the program has some more details.")), file=sys.stderr)
        except AttributeError:
            pass
        for filename in lessonfile.infocache.frontpage.iter_old_format_files():
            gu.dialog_ok(_("Cannot load front page file"), self,
                _("The file «%s» is saved in an old file format. The file can be converted by editing and saving it with an older version of Solfege. Versions from 3.16.0 to 3.20.4 should do the job.") % filename)

    def activate_exercise(self, module, urlobj=None):
        self.show_view(module)
        # We need this test because not all exercises use a notebook.
        if self.get_view().g_notebook:
            if urlobj and urlobj.action in ['practise', 'config', 'statistics']:
                self.get_view().g_notebook.set_current_page(
                   ['practise', 'config', 'statistics'].index(urlobj.action))
            else:
                self.get_view().g_notebook.set_current_page(0)
        self.set_title("Solfege - " + self.get_view().m_t.m_P.header.title)

    def display_docfile(self, fn):
        """
        Display the HTML file named by fn in the help browser window.
        """
        for lang in solfege.app.m_userman_language, "C":
            filename = os.path.join(os.getcwd(), "help", lang, fn)
            if os.path.isfile(filename):
                break
        try:
            webbrowser.open(filename)
        except Exception as e:
            self.display_error_message2(_("Error opening web browser"), str(e))

    def display_user_exercises(self, w):
        self.set_title("GNU Solfege - " + _("User Exercises"))
        if not self.show_view('userview'):
            self.add_view(UserView(""), 'userview')
            self.get_view().g_searchentry.grab_focus()
            self.get_view().on_search()
        else:
            self.show_view('userview')
        col = frontpage.Column()
        page = frontpage.Page(_('User Exercises'), col)
        curdir = None
        linklist = None
        d = os.path.join(filesystem.user_data(), "exercises/user/lesson-files")
        linklist = frontpage.LinkList(d)
        col.append(linklist)
        for filename in lessonfile.infocache.iter_user_files(only_user_collection=True):
            linklist.append(filename)
        self.get_view().display_data(page)

    def display_recent_exercises(self, w):
        data = frontpage.Page(_('_Recent Exercises').replace("_", ""),
            [frontpage.Column(
                [frontpage.LinkList(_('_Recent Exercises').replace("_", ""),
                   solfege.db.recent(8))])])
        self.display_frontpage(data, show_topics=True)
        self.set_title("GNU Solfege - " + _("_Recent Exercises").replace("_", ""))
        self.get_view().g_searchbox.hide()

    def display_recent_tests(self, w):
        data = frontpage.Page(_('_Recent Tests').replace("_", ""),
            [frontpage.Column(
                [frontpage.LinkList(_('_Recent Tests').replace("_", ""),
                   solfege.db.recent_tests(8))])])
        self.display_testpage(data, show_topics=True)
        self.get_view().g_searchbox.hide()
        self.set_title("GNU Solfege - " + _('_Recent Tests').replace("_", ""))

    def display_testpage(self, data=None, show_topics=False):
        """
        Display the front page of the data  in solfege.app.m_frontpage_data
        """
        self.set_title("GNU Solfege - " + _("Tests"))
        if not self.show_view('testspage'):
            p = TestsView()
            p.connect('link-clicked', self.history_handler)
            self.add_view(p, 'testspage')
        self.get_view().g_searchbox.show()
        if not data:
            data = solfege.app.m_frontpage_data
        self.trim_history(self.get_view(), data)
        self.get_view().display_data(data, show_topics=show_topics)

    def on_search_all_exercises(self, widget=None):
        self.set_title("GNU Solfege")
        if not self.show_view('searchview'):
            self.add_view(SearchView(_('Search the exercise titles of all lesson files found by the program, not just the active front page with sub pages.')), 'searchview')
        self.get_view().g_searchentry.grab_focus()

    def display_frontpage(self, data=None, show_topics=False):
        """
        Display the front page of the data  in solfege.app.m_frontpage_data
        """
        if solfege.app.m_options.profile:
            self.set_title("GNU Solfege - %s" % solfege.app.m_options.profile)
        else:
            self.set_title("GNU Solfege")
        if not self.show_view('frontpage'):
            p = FrontPage()
            p.connect('link-clicked', self.history_handler)
            self.add_view(p, 'frontpage')
        self.get_view().g_searchbox.show()
        if not data:
            data = solfege.app.m_frontpage_data
        self.trim_history(self.get_view(), data)
        self.get_view().display_data(data, show_topics=show_topics)

    def trim_history(self, new_viewer, new_page):
        # First check if the page we want to display is in m_history.
        # If so, we will trunkate history after it.
        for i, (viewer, page) in enumerate(self.m_history):
            if (new_viewer != viewer) or (new_page == page):
                self.m_history = self.m_history[:i]
                break

    def history_handler(self, *w):
        self.m_history.append(w)

    def initialise_exercise(self, teacher):
        """
        Create a Gui object for the exercise and add it to
        the box_dict dict.
        """
        assert teacher.m_exname not in self.box_dict
        self.get_view().hide()
        m = solfege.app.import_module(teacher.m_exname)
        self.add_view(m.Gui(teacher), teacher.m_exname)

    def on_key_press_event(self, widget, event):
        try:
            view = self.get_view()
        except KeyError:
            return
        if (event.type == Gdk.EventType.KEY_PRESS
            and event.get_state() & Gdk.ModifierType.MOD1_MASK == Gdk.ModifierType.MOD1_MASK  # Alt key
            and event.keyval in (Gdk.KEY_KP_Left, Gdk.KEY_Left)
            and self.m_history
            and not solfege.app.m_test_mode):
            obj, page = self.m_history[-1]
            self.trim_history(obj, page)
            # Find the box_dict key for obj
            for k, o in list(self.box_dict.items()):
                if o == obj:
                    obj.display_data(page)
                    self.show_view(k)
                    break
            return True
        view.on_key_press_event(widget, event)

    def run_startup_profile_manager(self):
        """
        Select a user profile to use. Return its name.
        Quit program if user selects that.
        """
        p = ProfileManager(self, cfg.get_string("app/last_profile"))
        ret = p.run()
        if ret == Gtk.ResponseType.ACCEPT:
            profile = p.get_profile()
            cfg.set_string("app/last_profile", "" if not profile else profile)
            p.destroy()
            return profile
        else:
            self.quit_program()

    def open_profile_manager(self, widget=None):
        p = ChangeProfileDialog(self, solfege.app.m_options.profile)
        if p.run() == Gtk.ResponseType.ACCEPT:
            prof = p.get_profile()
        else:
            # The user presses cancel. This will use the same profile as
            # before, but if the user has renamed the active profile, then
            # we need to use the new name.
            prof = p.m_default_profile
        p.destroy()
        solfege.app.reset_exercise()
        solfege.app.m_options.profile = prof
        solfege.db.conn.commit()
        solfege.db.conn.close()
        if prof is None:
            prof = ''
        solfege.db = statistics.DB(None, profile=prof)
        cfg.set_string("app/last_profile", prof)
        self.display_frontpage()

    def open_preferences_window(self, widget=None):
        if not self.g_config_window:
            self.g_config_window = ConfigWindow()
            self.g_config_window.show()
        else:
            self.g_config_window.update_old_statistics_info()
            self.g_config_window.update_statistics_info()
            self.g_config_window.show()

    def quit_program(self, *w):
        can_quit = True
        for dlg in list(gu.EditorDialogBase.instance_dict.values()):
            if dlg.close_window():
                dlg.destroy()
            else:
                can_quit = False
                break
        if can_quit:
            solfege.app.quit_program()
            gtk_application = self.get_application()
            if gtk_application:
                gtk_application.quit()
            else:
                self.destroy()
        else:
            return True

    def display_in_musicviewer(self, music):
        if not self.g_musicviewer_window:
            self.g_musicviewer_window = MusicViewerWindow(self)
            self.g_musicviewer_window.show()
        self.g_musicviewer_window.display_music(music)

    def close_musicviewer(self, widget=None):
        self.g_musicviewer_window.destroy()
        self.g_musicviewer_window = None

    def enter_test_mode(self):
        if 'enter_test_mode' not in dir(self.get_view()):
            gu.dialog_ok(_("The '%s' exercise module does not support test yet." % self.m_viewer), self)
            return
        for widget in self._not_exit_widgets:
            widget.set_sensitive(False)
        self.g = self.get_view().g_notebook.get_nth_page(0)
        self.get_view().g_notebook.remove(self.g)
        self.main_box.pack_start(self.g, True, True, 0)
        self.get_view().g_notebook.hide()
        self.get_view().enter_test_mode()

    def exit_test_mode(self):
        solfege.app.m_test_mode = False
        for widget in self._not_exit_widgets:
            widget.set_sensitive(True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.get_view().g_notebook.insert_page(box, Gtk.Label(label=_("Practise")), 0)
        self.main_box.remove(self.g)
        box.pack_start(self.g, True, True, 0)
        self.get_view().g_notebook.show()
        self.get_view().g_notebook.get_nth_page(0).show()
        self.get_view().g_notebook.set_current_page(0)
        self.get_view().exit_test_mode()

    def new_training_set_editor(self, widget):
        dlg = TrainingSetDialog()
        dlg.show_all()

    def new_practisesheet_editor(self, widget):
        dlg = PractiseSheetDialog()
        dlg.show_all()
