"""Developer smoke test for GTK windows not covered by the unit suite."""

import sys
import traceback
import warnings

from gi.repository import GLib, Gtk

import solfege
from solfege import fpeditor
from solfege.configwindow import ConfigWindow
from solfege.practisesheetdlg import PractiseSheetDialog
from solfege.profilemanager import (ChangeProfileDialog, NewProfileDialog,
                                    RenameProfileDialog)
from solfege.trainingsetdlg import TrainingSetDialog


# Python 3.14 deprecates asyncio policy APIs that the installed PyGObject
# event-loop adapter still queries. Keep the smoke output focused on Solfege.
warnings.filterwarnings('ignore', category=DeprecationWarning,
                        module=r'gi\.events')


def _drain_events():
    context = GLib.MainContext.default()
    # A mapped window may continuously schedule frame-clock work, so this
    # deliberately drains a bounded number of ready sources.
    for unused in range(50):
        if not context.pending():
            break
        context.iteration(False)


def _show_and_destroy(window):
    print("GTK 3 smoke: %s" % type(window).__name__, flush=True)
    window.set_transient_for(solfege.win)
    window.show_all()
    _drain_events()
    window.destroy()
    _drain_events()


def _close_editor(window):
    _show_and_destroy(window)
    key = window.get_idict_key()
    if key in window.instance_dict:
        del window.instance_dict[key]


def _close_about_dialog():
    if solfege.win.g_about_window:
        solfege.win.g_about_window.response(Gtk.ResponseType.CLOSE)
    return False


def run():
    try:
        preferences = ConfigWindow()
        _show_and_destroy(preferences)
        solfege.win.g_config_window = None

        solfege.win.show_path_info(None)
        _drain_events()
        solfege.win.g_path_info_dlg.destroy()
        solfege.win.g_path_info_dlg = None

        _show_and_destroy(NewProfileDialog())
        _show_and_destroy(RenameProfileDialog("GTK 3 smoke test"))
        _show_and_destroy(ChangeProfileDialog(solfege.win, None))

        _close_editor(TrainingSetDialog())
        _close_editor(PractiseSheetDialog())
        _close_editor(fpeditor.Editor())

        GLib.timeout_add(10, _close_about_dialog)
        solfege.win.show_about_window(None)

        for lesson in (
                "solfege:lesson-files/harmonic-intervals-3",
                "solfege:lesson-files/rhythm-easy",
                "solfege:lesson-files/jsb-inventions",
                "solfege:lesson-files/id-tone-cde-3",
                "solfege:lesson-files/nameinterval-2",
                "solfege:lesson-files/toneincontext-major-f4"):
            solfege.app.practise_lessonfile(lesson)
            _drain_events()

        print("GTK 3 smoke: test-mode layout", flush=True)
        solfege.app.test_lessonfile(
            "solfege:lesson-files/harmonic-intervals-3")
        _drain_events()
        solfege.win.exit_test_mode()
        _drain_events()

        print("GTK 3 smoke test passed")
    except Exception:
        solfege.gtk3_smoke_test_failed = True
        traceback.print_exc(file=sys.__stderr__)
    finally:
        solfege.win.quit_program()
    return False
