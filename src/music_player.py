"""
Music player module for Flip or FlOOP.

Provides a static utility class that handles background music playback
using the Windows Multimedia API (``winmm.dll``).

.. note::
    This module is **Windows-only** because it relies on
    ``ctypes.windll.winmm.mciSendStringW``.  On other platforms
    the music will silently not play and a warning will be logged.
"""

import os
import sys
import ctypes
from utils import get_asset_path, setup_logger

_logger = setup_logger("music_player")


class MusicPlayer:
    """
    Static utility class for background music playback.

    All methods are ``@staticmethod`` — no instance is needed.  Internally
    uses the MCI (Media Control Interface) string commands on Windows to
    open, loop, and stop an audio file under the alias ``bgmusic``.

    Typical usage::

        MusicPlayer.play("music.mp3")   # starts looped playback
        MusicPlayer.stop()              # stops and releases the resource
    """

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    @staticmethod
    def _is_windows() -> bool:
        """Return ``True`` if the current platform is Windows."""
        return sys.platform.startswith("win")

    @staticmethod
    def _mci_send(command: str) -> int:
        """
        Send an MCI string command and return the result code.

        Args:
            command: The MCI command string (e.g. ``"play bgmusic repeat"``).

        Returns:
            The integer return code from ``mciSendStringW`` (0 = success).
        """
        return ctypes.windll.winmm.mciSendStringW(command, None, 0, 0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def play(filename: str = "music.mp3") -> None:
        """
        Start looped playback of an audio file.

        If *filename* is not an absolute path it is resolved via
        :func:`utils.get_asset_path`.  Any previously playing music
        under the ``bgmusic`` alias is stopped first.

        Args:
            filename: Path or basename of the audio file to play.
                      Defaults to ``"music.mp3"``.
        """
        if not MusicPlayer._is_windows():
            _logger.warning(
                "Music playback is only supported on Windows. "
                "Skipping playback of '%s'.",
                filename,
            )
            return

        # Resolve relative filenames to the assets directory.
        if not os.path.isabs(filename):
            try:
                filename = get_asset_path(filename)
            except (FileNotFoundError, ValueError) as exc:
                _logger.error("Cannot resolve music file: %s", exc)
                return

        if not os.path.exists(filename):
            _logger.error("Music file does not exist: %s", filename)
            return

        try:
            abs_path = os.path.abspath(filename)

            # Close any previously opened instance to avoid conflicts.
            MusicPlayer._mci_send("close bgmusic")

            # Open the file using the mpegvideo driver (handles mp3 & wav).
            result = MusicPlayer._mci_send(
                f'open "{abs_path}" type mpegvideo alias bgmusic'
            )
            if result != 0:
                _logger.error(
                    "MCI open failed with code %d for file: %s",
                    result,
                    abs_path,
                )
                return

            # Begin looped playback.
            result = MusicPlayer._mci_send("play bgmusic repeat")
            if result != 0:
                _logger.error("MCI play failed with code %d.", result)
                return

            _logger.info("Now playing: %s", abs_path)

        except Exception:
            _logger.exception("Unexpected error while starting music playback.")

    @staticmethod
    def stop() -> None:
        """
        Stop playback and release the ``bgmusic`` MCI alias.

        Safe to call even if nothing is currently playing.
        """
        if not MusicPlayer._is_windows():
            return

        try:
            MusicPlayer._mci_send("stop bgmusic")
            MusicPlayer._mci_send("close bgmusic")
            _logger.info("Music stopped.")
        except Exception:
            _logger.exception("Unexpected error while stopping music playback.")
