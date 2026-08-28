# GNU Solfege — GTK 3 and Python 3 Fork

GNU Solfege is an ear-training application for practising intervals,
rhythms, chords, scales, and music theory.

> [!IMPORTANT]
> This is an unofficial, community-maintained modernization fork. It is not
> an official GNU Solfege release.

## Status

This fork modernizes GNU Solfege 3.23 for current Linux desktops. It has been
tested with:

- Python 3.14.4
- GTK 3.24.52
- PyGObject 3.56.2
- KDE Plasma 6 on Wayland

The modernization includes:

- A native `Gtk.Application` lifecycle
- A KDE Plasma-compatible in-window menu bar
- Replacement of deprecated GTK stock, `Gtk.UIManager`, and widget APIs
- Current GTK 3 widgets and GDK enums
- Python 3.14 compatibility
- A modernized standalone lesson-file editor
- Automatic TiMidity SoundFont selection

GTK 4 is not currently supported.

## Installation

### Debian and Ubuntu

Install the runtime and source-bootstrap dependencies:

```bash
sudo apt update
sudo apt install \
  git python3 python3-gi python3-cairo gir1.2-gtk-3.0 \
  autoconf automake build-essential gettext \
  timidity timgm6mb-soundfont
```

Clone your GitHub repository and enter the source directory:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/gnu-solfege.git
cd gnu-solfege
```

Replace `YOUR_GITHUB_USERNAME` with the account or organization that hosts
the fork.

Generate the files omitted from a Git checkout:

```bash
./autogen.sh
MAKEINFO=/bin/true ./configure --disable-oss-sound
make solfege/languages.py
```

Start Solfege from the source tree:

```bash
./solfege.py
```

To troubleshoot startup without initializing audio, use:

```bash
./solfege.py --no-sound
```

## Lesson-file editor

The standalone lesson-file editor can be started with:

```bash
./lessonfile_editor.py
```

## Testing

Run the unit test suite:

```bash
python3 test.py
```

Run the automated GTK 3 GUI smoke test:

```bash
./solfege.py --gtk3-smoke-test
```

The current test suite contains 287 passing tests. The smoke test opens and
closes representative windows, dialogs, editors, exercises, and test-mode
layouts.

## Sound

The default source-tree configuration uses TiMidity for MIDI playback. This
fork automatically selects a supported installed General MIDI SoundFont,
including TimGM6mb and FluidR3 GM configurations.

Audio playback can be configured from Solfege's preferences window.

## Optional software

Some specialized features require additional programs:

- [LilyPond](https://lilypond.org/) for printable practice sheets
- [Csound](https://csound.com/) for Csound-based exercises
- [MMA](https://www.mellowood.ca/mma/) for accompaniment-based exercises
- PyALSA for direct ALSA sequencer output

These programs are not required for the standard TiMidity-based exercises.

## Known limitations

- Linux is currently the only tested operating system.
- Windows and macOS have not been validated.
- The project retains its original Autoconf-based build system.
- This is a GTK 3 modernization, not a GTK 4 port.
- Optional OSS, tuner, PyALSA, Csound, MMA, and printing paths have less
  coverage than the standard GTK and TiMidity paths.

## Upstream and credits

GNU Solfege was created by Tom Cato Amundsen and developed as part of the GNU
Project. This repository preserves the original history and adds compatibility
work for current Python, GTK, PyGObject, KDE Plasma, and Wayland environments.

- [Official GNU Solfege project](https://www.gnu.org/software/solfege/)
- [Upstream GNU Savannah repository](https://git.savannah.gnu.org/git/solfege.git)
- [GNU Solfege release archive](https://ftp.gnu.org/gnu/solfege/)

Please report problems with this modernization fork to the issue tracker of
the GitHub repository hosting it. Upstream GNU contact addresses should not be
used for fork-specific bugs unless the issue is reproduced in upstream code.

## License

GNU Solfege is free software distributed under the GNU General Public License.
See [COPYING](COPYING) and the individual source-file headers for the exact
terms applying to each file.
