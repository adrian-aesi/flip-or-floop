"""
Record manager module for Flip or FlOOP.

Handles loading and saving the player's best completion times (records)
to a JSON file on disk.  Records are tracked independently for each
difficulty mode (``"easy"`` and ``"hard"``).

File format (``records.json``)::

    {
        "easy": "00:22",
        "hard": "01:15"
    }

A ``null`` value (or missing key) indicates no record has been set yet
for that mode.
"""

import os
import json
from typing import Optional
from utils import BASE_DIR, setup_logger

_logger = setup_logger("record_manager")

# The set of valid mode keys.  Used for input validation.
_VALID_MODES: frozenset[str] = frozenset({"easy", "hard"})

_NO_RECORD_PLACEHOLDER: str = "--:--"
"""Display string returned when no record exists for a mode."""


class RecordManager:
    """
    Manages persistent best-time records stored as JSON.

    On construction the records file is loaded (if it exists).  When a
    new record is set via :meth:`save_record` the file is written back
    to disk immediately.

    Attributes:
        filename: Absolute path to the JSON records file.
        records:  Dictionary mapping mode names to their best time
                  strings (e.g. ``{"easy": "00:22", "hard": None}``).
    """

    def __init__(self, filename: str = "records.json") -> None:
        """
        Initialise the record manager and load existing records.

        Args:
            filename: Path to the records file.  If not absolute it is
                      resolved relative to the project root directory.
        """
        if not os.path.isabs(filename):
            filename = os.path.join(BASE_DIR, filename)

        self.filename: str = filename
        self.records: dict[str, Optional[str]] = {"easy": None, "hard": None}
        self._load_records()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_records(self) -> None:
        """
        Load records from the JSON file on disk.

        If the file does not exist or contains invalid JSON the records
        dictionary is left at its default values and a warning is logged.
        """
        if not os.path.exists(self.filename):
            _logger.info(
                "Records file not found at '%s'. Starting with empty records.",
                self.filename,
            )
            return

        try:
            with open(self.filename, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            if not isinstance(data, dict):
                _logger.warning(
                    "Records file does not contain a JSON object. "
                    "Ignoring contents of '%s'.",
                    self.filename,
                )
                return

            # Only accept known mode keys to protect against corrupt data.
            for mode in _VALID_MODES:
                value = data.get(mode)
                if value is not None and not self._is_valid_time_str(value):
                    _logger.warning(
                        "Invalid time string '%s' for mode '%s'. Ignoring.",
                        value,
                        mode,
                    )
                    continue
                self.records[mode] = value

            _logger.info("Records loaded from '%s': %s", self.filename, self.records)

        except json.JSONDecodeError as exc:
            _logger.error(
                "Failed to parse records file '%s': %s. "
                "Starting with empty records.",
                self.filename,
                exc,
            )
        except OSError as exc:
            _logger.error(
                "Could not read records file '%s': %s. "
                "Starting with empty records.",
                self.filename,
                exc,
            )

    def _write_records(self) -> None:
        """
        Persist the current records dictionary to disk as JSON.

        Raises:
            OSError: If the file cannot be written (logged, not re-raised).
        """
        try:
            with open(self.filename, "w", encoding="utf-8") as fh:
                json.dump(self.records, fh, indent=2)
            _logger.debug("Records written to '%s'.", self.filename)
        except OSError as exc:
            _logger.error(
                "Failed to write records file '%s': %s", self.filename, exc
            )

    @staticmethod
    def _is_valid_time_str(time_str: str) -> bool:
        """
        Check whether *time_str* matches the ``MM:SS`` format.

        Args:
            time_str: The string to validate.

        Returns:
            ``True`` if valid, ``False`` otherwise.
        """
        if not isinstance(time_str, str):
            return False
        parts = time_str.split(":")
        if len(parts) != 2:
            return False
        try:
            mins, secs = int(parts[0]), int(parts[1])
            return mins >= 0 and 0 <= secs < 60
        except ValueError:
            return False

    @staticmethod
    def _to_seconds(time_str: str) -> int:
        """
        Convert a ``"MM:SS"`` string to total seconds.

        Args:
            time_str: A time string in ``MM:SS`` format.

        Returns:
            The equivalent number of seconds, or ``999_999`` if the
            string cannot be parsed (ensures an invalid time never
            "wins" a comparison).
        """
        try:
            mins, secs = map(int, time_str.split(":"))
            return mins * 60 + secs
        except (ValueError, AttributeError):
            _logger.warning("Could not parse time string: '%s'", time_str)
            return 999_999

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_record(self, mode: str, time_str: str) -> None:
        """
        Save a new record if it beats the current best for *mode*.

        The record is only updated (and persisted) when *time_str*
        represents a shorter time than the existing record, or when no
        record has been set yet.

        Args:
            mode:     The difficulty mode (``"easy"`` or ``"hard"``).
            time_str: The completion time in ``"MM:SS"`` format.

        Raises:
            ValueError: If *mode* is not a recognised difficulty or
                        *time_str* is not a valid ``MM:SS`` string.
        """
        if mode not in _VALID_MODES:
            raise ValueError(
                f"Unknown mode '{mode}'. Expected one of {sorted(_VALID_MODES)}."
            )

        if not self._is_valid_time_str(time_str):
            raise ValueError(
                f"Invalid time string '{time_str}'. Expected format 'MM:SS'."
            )

        current = self.records.get(mode)
        if current is None or self._to_seconds(time_str) < self._to_seconds(current):
            old_display = current or _NO_RECORD_PLACEHOLDER
            _logger.info(
                "New record for '%s': %s (was %s).", mode, time_str, old_display
            )
            self.records[mode] = time_str
            self._write_records()
        else:
            _logger.debug(
                "Time %s did not beat current record %s for '%s'.",
                time_str,
                current,
                mode,
            )

    def get_record(self, mode: str) -> str:
        """
        Return the best time string for *mode*, or a placeholder.

        Args:
            mode: The difficulty mode (``"easy"`` or ``"hard"``).

        Returns:
            The best time as ``"MM:SS"``, or ``"--:--"`` if no record
            exists or the mode is unrecognised.
        """
        record = self.records.get(mode)
        if record is None:
            return _NO_RECORD_PLACEHOLDER
        return record
