"""
About screen module for Flip or FlOOP.

Shows a parchment-styled overlay with:

* A brief explanation of how the game works.
* The player's best-time records for each difficulty mode.
* Team credits.
* A "Back to Main Menu" button.
"""

import tkinter as tk
from PIL import Image, ImageTk

from utils import (
    get_asset_path,
    setup_logger,
    WINDOW_SIZE,
    COLOR_PARCHMENT,
    COLOR_BROWN_DARK,
    COLOR_TAN_BUTTON,
    COLOR_TAN_BUTTON_ACTIVE,
    COLOR_TEXT_DARK,
    COLOR_TEXT_CREDITS,
    COLOR_TEXT_ITALIC,
)
from record_manager import RecordManager

_logger = setup_logger("about_screen")

# --- Credits & explanation (kept out of the class for easy editing) ---

_EXPLANATION_TEXT: str = (
    "Welcome to flip or flOOP, the memory game that tests your brainpower!\n\n"
    "Choose your difficulty: flipling mode (4×4) or Wild Mind Maze (6×6).\n\n"
    "Flip two cards – match them to keep them revealed.\n\n"
    "The goal: match all pairs and set a new record!"
)

_CREDITS_TEXT: str = (
    "Adrian Chavez — Project Manager\n"
    "David Antonio — Lead Engineer\n"
    "Jefferson Janer — Senior Dev\n"
    "Janssen Rosalin — Junior Dev\n"
    "Stephen Marinas — QA Engineer"
)


class AboutScreen(tk.Frame):
    """
    Full-screen frame containing the About / Credits overlay.

    Renders a parchment-styled card over the jungle background with
    game instructions, best-time records pulled from the
    :class:`~record_manager.RecordManager`, team credits, and a
    navigation button back to the main menu.

    Args:
        parent:         The parent Tk widget (typically the root window).
        record_manager: A :class:`RecordManager` instance used to read
                        the player's best times.
        back_callback:  Callable invoked when the "Back to Main Menu"
                        button is pressed.
    """

    def __init__(
        self,
        parent: tk.Misc,
        record_manager: RecordManager,
        back_callback,
    ) -> None:
        super().__init__(parent)

        _logger.info("Opening About screen.")

        # --- Background image ---
        try:
            self.bg_image = Image.open(get_asset_path("background.png")).resize(WINDOW_SIZE)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except (FileNotFoundError, OSError) as exc:
            _logger.error("Could not load background image: %s", exc)
            self.configure(bg=COLOR_PARCHMENT)

        # --- Overlay container (parchment card) ---
        self.container = tk.Frame(
            self,
            bg=COLOR_PARCHMENT,
            highlightthickness=3,
            highlightbackground=COLOR_BROWN_DARK,
        )
        self.container.place(relx=0.5, rely=0.5, anchor="center", width=480)

        # --- Title ---
        tk.Label(
            self.container,
            text="About",
            font=("Arial", 24, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        ).pack(pady=(18, 8))

        self._add_separator()

        # --- Game explanation ---
        tk.Label(
            self.container,
            text=_EXPLANATION_TEXT,
            wraplength=420,
            justify="center",
            font=("Arial", 11),
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_DARK,
        ).pack(pady=(4, 10))

        # --- Records section ---
        self._add_separator()

        tk.Label(
            self.container,
            text="🏆 Records",
            font=("Arial", 18, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        ).pack(pady=(4, 6))

        easy_record = record_manager.get_record("easy")
        hard_record = record_manager.get_record("hard")

        records_frame = tk.Frame(self.container, bg=COLOR_PARCHMENT)
        records_frame.pack(pady=(0, 8))

        tk.Label(
            records_frame,
            text=f"flipling mode (4×4):  {easy_record}",
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_DARK,
            font=("Arial", 12),
        ).pack(anchor="w", padx=20)

        tk.Label(
            records_frame,
            text=f"Wild Mind Maze (6×6):  {hard_record}",
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_DARK,
            font=("Arial", 12),
        ).pack(anchor="w", padx=20, pady=(2, 0))

        # --- Credits section ---
        self._add_separator()

        tk.Label(
            self.container,
            text="Thanks for playing our OOP project!",
            font=("Arial", 11, "italic"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_ITALIC,
        ).pack(pady=(4, 6))

        tk.Label(
            self.container,
            text=_CREDITS_TEXT,
            justify="center",
            font=("Arial", 11),
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_CREDITS,
        ).pack(pady=(0, 10))

        # --- Back button ---
        tk.Button(
            self.container,
            text="Back to Main Menu",
            font=("Arial", 14, "bold"),
            bg=COLOR_TAN_BUTTON,
            fg="white",
            activebackground=COLOR_TAN_BUTTON_ACTIVE,
            activeforeground="white",
            command=back_callback,
            bd=3,
            relief="solid",
            width=18,
            cursor="hand2",
        ).pack(pady=(6, 18), ipady=3)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _add_separator(self) -> None:
        """Insert a thin horizontal separator line into the container."""
        tk.Frame(self.container, bg=COLOR_BROWN_DARK, height=2).pack(
            fill="x", padx=40, pady=(0, 10)
        )
