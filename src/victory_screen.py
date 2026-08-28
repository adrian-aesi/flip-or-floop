"""
Victory screen module for Flip or FlOOP.

Displays a congratulatory overlay after the player has matched all card
pairs, showing the completion time and mode.  Offers "Replay" and
"Main Menu" buttons for navigation.
"""

import tkinter as tk
from PIL import Image, ImageTk

from utils import (
    get_asset_path,
    setup_logger,
    WINDOW_SIZE,
    COLOR_PARCHMENT,
    COLOR_BROWN_DARK,
    COLOR_BROWN_BUTTON,
    COLOR_BROWN_BUTTON_ACTIVE,
    COLOR_TAN_BUTTON,
    COLOR_TAN_BUTTON_ACTIVE,
    COLOR_TEXT_DARK,
)

_logger = setup_logger("victory_screen")

# Friendly names shown to the player for each difficulty mode.
_MODE_DISPLAY_NAMES: dict[str, str] = {
    "easy": "flipling mode",
    "hard": "Wild Mind Maze",
}


class VictoryScreen(tk.Frame):
    """
    Full-screen frame displayed when the player wins a game.

    Shows the completion time, difficulty mode, and two action buttons:
    *Replay* (restarts the same mode) and *Main Menu* (returns to the
    home screen).

    Args:
        parent:          The parent Tk widget (typically the root window).
        time_str:        The player's completion time in ``"MM:SS"`` format.
        mode:            The difficulty mode that was just completed
                         (``"easy"`` or ``"hard"``).
        replay_callback: Called when the player clicks **Replay**.
        back_callback:   Called when the player clicks **Main Menu**.
    """

    def __init__(
        self,
        parent: tk.Misc,
        time_str: str,
        mode: str,
        replay_callback,
        back_callback,
    ) -> None:
        super().__init__(parent)

        _logger.info(
            "Displaying victory screen — mode='%s', time='%s'.", mode, time_str
        )

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
        self.container.place(relx=0.5, rely=0.5, anchor="center", width=420, height=300)

        # --- Victory title ---
        tk.Label(
            self.container,
            text="🎉 You Win! 🎉",
            font=("Arial", 28, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        ).pack(pady=(24, 10))

        # --- Completion info ---
        mode_name = _MODE_DISPLAY_NAMES.get(mode, mode)
        tk.Label(
            self.container,
            text=f"Completed {mode_name} in {time_str}!",
            font=("Arial", 14),
            bg=COLOR_PARCHMENT,
            fg=COLOR_TEXT_DARK,
        ).pack(pady=(4, 16))

        # --- Action buttons ---
        button_frame = tk.Frame(self.container, bg=COLOR_PARCHMENT)
        button_frame.pack(pady=(4, 20))

        btn_opts: dict = dict(
            font=("Arial", 14, "bold"),
            width=11,
            bd=2,
            relief="solid",
            cursor="hand2",
        )

        replay_btn = tk.Button(
            button_frame,
            text="Replay",
            bg=COLOR_BROWN_BUTTON,
            fg="white",
            activebackground=COLOR_BROWN_BUTTON_ACTIVE,
            activeforeground="white",
            command=replay_callback,
            **btn_opts,
        )
        replay_btn.pack(side="left", padx=10, ipady=3)

        back_btn = tk.Button(
            button_frame,
            text="Main Menu",
            bg=COLOR_TAN_BUTTON,
            fg="white",
            activebackground=COLOR_TAN_BUTTON_ACTIVE,
            activeforeground="white",
            command=back_callback,
            **btn_opts,
        )
        back_btn.pack(side="left", padx=10, ipady=3)
