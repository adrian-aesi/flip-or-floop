"""
Game screen module for Flip or FlOOP.

Contains the four UI components that together make up the gameplay
experience:

* :class:`TimerScreen` — an auto-updating ``MM:SS`` stopwatch.
* :class:`CardScreen`  — the card grid with flip/match logic.
* :class:`PauseOverlay` — a modal overlay shown while the game is paused.
* :class:`GameScreen`  — the top-level composite that wires everything
  together (background, timer, cards, pause button).
"""

import tkinter as tk
import time
import random
from typing import Optional

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
)
from record_manager import RecordManager

_logger = setup_logger("game_screen")

# ---------------------------------------------------------------------------
# Card-size presets per difficulty mode
# ---------------------------------------------------------------------------

_CARD_CONFIG: dict[str, dict] = {
    "easy": {"card_size": 110, "card_pad": 5, "grid_size": 4},
    "hard": {"card_size": 80,  "card_pad": 3, "grid_size": 6},
}
"""Per-mode visual configuration for card dimensions and grid layout."""

_FLIP_DELAY_MS: int = 800
"""Milliseconds to wait before flipping non-matching cards back."""


# ===================================================================
# Timer UI
# ===================================================================

class TimerScreen(tk.Frame):
    """
    A simple stopwatch widget that counts up from ``00:00``.

    The timer starts automatically on construction and updates every
    second.  It can be stopped via :meth:`stop` and its elapsed time
    retrieved via :meth:`get_elapsed_time`.

    Args:
        parent_frame: The parent Tk widget to embed this timer in.
    """

    def __init__(self, parent_frame: tk.Misc) -> None:
        super().__init__(parent_frame, bg=COLOR_PARCHMENT)

        self.start_time: float = time.time()
        self.running: bool = True

        self.timer_label = tk.Label(
            self,
            font=("Arial", 16, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        )
        self.timer_label.pack(pady=(6, 4))
        self._tick()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Update the label text every second while the timer is running."""
        if self.running:
            elapsed = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed, 60)
            self.timer_label.config(text=f"Time: {minutes:02}:{seconds:02}")
            self.after(1000, self._tick)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_elapsed_time(self) -> str:
        """
        Return the elapsed time formatted as ``"MM:SS"``.

        Returns:
            A string such as ``"01:23"``.
        """
        elapsed = int(time.time() - self.start_time)
        minutes, seconds = divmod(elapsed, 60)
        return f"{minutes:02}:{seconds:02}"

    def stop(self) -> None:
        """Stop the timer from updating further."""
        self.running = False
        _logger.debug("Timer stopped at %s.", self.get_elapsed_time())


# ===================================================================
# Card Grid UI
# ===================================================================

class CardScreen(tk.Frame):
    """
    Renders the grid of face-down cards and handles flip / match logic.

    Two cards may be face-up at a time.  After a short delay
    (:data:`_FLIP_DELAY_MS`) they are either kept (if they match) or
    flipped back.  When every pair is matched the game ends and the
    victory screen is shown.

    Args:
        parent_frame:   The parent Tk widget.
        back_img:       The ``PhotoImage`` shown on the card back.
        front_imgs:     List of ``PhotoImage`` objects for card faces.
        mode:           ``"easy"`` (4×4) or ``"hard"`` (6×6).
        record_manager: :class:`RecordManager` used to save records.
        timer_screen:   The :class:`TimerScreen` driving the clock.
        app:            Reference to the main :class:`FlipOrFloopApp`
                        (used to navigate to the victory screen).
    """

    def __init__(
        self,
        parent_frame: tk.Misc,
        back_img: ImageTk.PhotoImage,
        front_imgs: list[ImageTk.PhotoImage],
        mode: str,
        record_manager: RecordManager,
        timer_screen: TimerScreen,
        app=None,
    ) -> None:
        super().__init__(parent_frame, bg=COLOR_PARCHMENT)

        self.back_img = back_img
        self.front_imgs = front_imgs
        self.mode = mode
        self.record_manager = record_manager
        self.timer_screen = timer_screen
        self.app = app

        # Look up card dimensions for this mode.
        config = _CARD_CONFIG.get(mode)
        if config is None:
            _logger.error(
                "Unknown mode '%s'; falling back to 'easy' card config.", mode
            )
            config = _CARD_CONFIG["easy"]

        self.card_size: int = config["card_size"]
        self.card_pad: int = config["card_pad"]
        self.grid_size: int = config["grid_size"]
        self.num_pairs: int = (self.grid_size ** 2) // 2

        # Game state
        self.card_buttons: list[tk.Button] = []
        self.card_data: list[dict] = []
        self.first_card: Optional[int] = None
        self.busy: bool = False    # True while waiting for the flip-back delay
        self.paused: bool = False  # True when the pause overlay is active

        self._build_board()
        _logger.info(
            "Card board created: %dx%d grid (%d pairs), mode='%s'.",
            self.grid_size,
            self.grid_size,
            self.num_pairs,
            self.mode,
        )

    # ------------------------------------------------------------------
    # Board setup
    # ------------------------------------------------------------------

    def _build_board(self) -> None:
        """
        Shuffle card IDs and create the grid of face-down card buttons.

        Each card gets a dictionary in :attr:`card_data` tracking its
        pair ``id``, whether it is currently ``flipped``, and whether
        it has been ``matched``.
        """
        card_ids = list(range(self.num_pairs)) * 2
        random.shuffle(card_ids)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                idx = row * self.grid_size + col
                btn = tk.Button(
                    self,
                    image=self.back_img,
                    command=lambda i=idx: self.flip_card(i),
                    width=self.card_size,
                    height=self.card_size,
                    bd=2,
                    relief="solid",
                    bg=COLOR_BROWN_DARK,
                    activebackground=COLOR_PARCHMENT,
                    cursor="hand2",
                )
                btn.grid(row=row, column=col, padx=self.card_pad, pady=self.card_pad)
                self.card_buttons.append(btn)
                self.card_data.append({
                    "id": card_ids[idx],
                    "flipped": False,
                    "matched": False,
                })

    # ------------------------------------------------------------------
    # Card interaction
    # ------------------------------------------------------------------

    def flip_card(self, idx: int) -> None:
        """
        Handle a click on the card at position *idx*.

        Ignores clicks when the board is busy (waiting for a flip-back),
        paused, or the card is already face-up / matched.

        Args:
            idx: Zero-based index into :attr:`card_buttons` / :attr:`card_data`.
        """
        if self.busy or self.paused:
            return

        if idx < 0 or idx >= len(self.card_data):
            _logger.warning("flip_card called with out-of-range index %d.", idx)
            return

        card = self.card_data[idx]
        if card["flipped"] or card["matched"]:
            return

        # Reveal the card face.
        self.card_buttons[idx].config(image=self.front_imgs[card["id"]])
        card["flipped"] = True

        if self.first_card is None:
            # This is the first card of a pair attempt.
            self.first_card = idx
        else:
            # Second card revealed — schedule the match check.
            self.busy = True
            second_idx = idx
            first_idx = self.first_card
            self.first_card = None
            self.after(_FLIP_DELAY_MS, self._check_match, first_idx, second_idx)

    def _check_match(self, idx1: int, idx2: int) -> None:
        """
        Compare two revealed cards and either keep or flip them back.

        If all pairs are matched, the timer is stopped, the record is
        saved, and the victory screen is shown.

        Args:
            idx1: Index of the first revealed card.
            idx2: Index of the second revealed card.
        """
        card1 = self.card_data[idx1]
        card2 = self.card_data[idx2]

        if card1["id"] == card2["id"]:
            # Match! Keep them face-up.
            card1["matched"] = True
            card2["matched"] = True
            _logger.debug("Match found: cards %d and %d (pair id=%d).", idx1, idx2, card1["id"])
        else:
            # No match — flip both back.
            self.card_buttons[idx1].config(image=self.back_img)
            self.card_buttons[idx2].config(image=self.back_img)
            card1["flipped"] = False
            card2["flipped"] = False

        self.busy = False

        # Check for game completion.
        if all(card["matched"] for card in self.card_data):
            time_str = self.timer_screen.get_elapsed_time()
            _logger.info("All pairs matched! Final time: %s.", time_str)
            self.timer_screen.stop()

            try:
                self.record_manager.save_record(self.mode, time_str)
            except ValueError as exc:
                _logger.error("Failed to save record: %s", exc)

            if self.app is not None:
                self.app.show_victory(time_str, self.mode)
            else:
                _logger.warning(
                    "No app reference — cannot navigate to victory screen."
                )

    # ------------------------------------------------------------------
    # Pause support
    # ------------------------------------------------------------------

    def set_paused(self, paused: bool) -> None:
        """
        Enable or disable the paused state.

        When paused, all unmatched card buttons are disabled so that
        they cannot be clicked.

        Args:
            paused: ``True`` to pause, ``False`` to resume.
        """
        self.paused = paused
        state = tk.DISABLED if paused else tk.NORMAL
        for idx, btn in enumerate(self.card_buttons):
            if not self.card_data[idx]["matched"]:
                btn.config(state=state)

        _logger.debug("Card screen paused=%s.", paused)


# ===================================================================
# Pause Overlay UI
# ===================================================================

class PauseOverlay(tk.Frame):
    """
    Modal overlay displayed on top of the game when the player pauses.

    Provides three actions: **Resume**, **Replay**, and **Main Menu**.

    Args:
        parent:          The parent Tk widget.
        timer_screen:    The active :class:`TimerScreen` (currently unused
                         but passed for possible future extensions).
        card_screen:     The active :class:`CardScreen` (same note).
        resume_callback: Called when the player clicks **Resume**.
        replay_callback: Called when the player clicks **Replay**.
        back_callback:   Called when the player clicks **Main Menu**.
    """

    def __init__(
        self,
        parent: tk.Misc,
        timer_screen: TimerScreen,
        card_screen: CardScreen,
        resume_callback,
        replay_callback,
        back_callback,
    ) -> None:
        super().__init__(
            parent,
            bg=COLOR_PARCHMENT,
            highlightthickness=3,
            highlightbackground=COLOR_BROWN_DARK,
        )

        self.timer_screen = timer_screen
        self.card_screen = card_screen

        tk.Label(
            self,
            text="⏸️ Game Paused",
            font=("Arial", 20, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        ).pack(pady=(18, 12))

        btn_font = ("Arial", 13, "bold")
        btn_opts: dict = dict(font=btn_font, width=16, bd=2, relief="solid", cursor="hand2")

        tk.Button(
            self,
            text="Resume",
            bg=COLOR_BROWN_BUTTON,
            fg="white",
            activebackground=COLOR_BROWN_BUTTON_ACTIVE,
            activeforeground="white",
            command=resume_callback,
            **btn_opts,
        ).pack(pady=6, ipady=3)

        tk.Button(
            self,
            text="Replay",
            bg=COLOR_TAN_BUTTON,
            fg="white",
            activebackground=COLOR_TAN_BUTTON_ACTIVE,
            activeforeground="white",
            command=replay_callback,
            **btn_opts,
        ).pack(pady=6, ipady=3)

        tk.Button(
            self,
            text="Main Menu",
            bg=COLOR_TAN_BUTTON,
            fg="white",
            activebackground=COLOR_TAN_BUTTON_ACTIVE,
            activeforeground="white",
            command=back_callback,
            **btn_opts,
        ).pack(pady=(6, 18), ipady=3)

        _logger.debug("Pause overlay created.")


# ===================================================================
# Main Game Screen (Composite)
# ===================================================================

class GameScreen(tk.Frame):
    """
    Top-level composite frame that assembles the full game view.

    Composes a :class:`TimerScreen`, a :class:`CardScreen`, and a
    **Pause** button over the jungle background.  Also manages the
    :class:`PauseOverlay` lifecycle (show / resume / replay / back).

    Args:
        parent:          The parent Tk widget (typically the root window).
        record_manager:  :class:`RecordManager` for saving records.
        back_img_path:   Path to the card-back image file.
        front_img_paths: List of paths to the card-face image files.
        mode:            ``"easy"`` or ``"hard"``.
        app:             Reference to the main :class:`FlipOrFloopApp`.
    """

    def __init__(
        self,
        parent: tk.Misc,
        record_manager: RecordManager,
        back_img_path: str,
        front_img_paths: list[str],
        mode: str = "easy",
        app=None,
    ) -> None:
        super().__init__(parent)

        self.parent = parent
        self.record_manager = record_manager
        self.mode = mode
        self.app = app
        self.pause_overlay: Optional[PauseOverlay] = None

        # Determine card pixel size from mode config.
        config = _CARD_CONFIG.get(mode)
        if config is None:
            _logger.error("Unknown mode '%s'; falling back to 'easy'.", mode)
            config = _CARD_CONFIG["easy"]
        card_size: int = config["card_size"]

        # --- Background image ---
        try:
            self.bg_image = Image.open(get_asset_path("background.png")).resize(WINDOW_SIZE)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except (FileNotFoundError, OSError) as exc:
            _logger.error("Could not load background image: %s", exc)
            self.configure(bg=COLOR_PARCHMENT)

        # --- Load card images ---
        try:
            self.back_img = ImageTk.PhotoImage(
                Image.open(back_img_path).resize((card_size, card_size))
            )
        except (FileNotFoundError, OSError) as exc:
            _logger.error("Could not load card-back image '%s': %s", back_img_path, exc)
            raise

        num_images: int = config["grid_size"] ** 2 // 2
        self.front_imgs_raw: list[Image.Image] = []
        self.front_imgs: list[ImageTk.PhotoImage] = []

        for path in front_img_paths[:num_images]:
            try:
                img = Image.open(path).resize((card_size, card_size))
                self.front_imgs_raw.append(img)
                self.front_imgs.append(ImageTk.PhotoImage(img))
            except (FileNotFoundError, OSError) as exc:
                _logger.error("Could not load card image '%s': %s", path, exc)
                raise

        if len(self.front_imgs) < num_images:
            _logger.error(
                "Not enough card images: need %d, got %d.",
                num_images,
                len(self.front_imgs),
            )
            raise ValueError(
                f"Expected at least {num_images} card-face images, "
                f"but only {len(self.front_imgs)} were loaded."
            )

        # --- Overlay container (parchment card) ---
        self.overlay_frame = tk.Frame(
            self,
            bg=COLOR_PARCHMENT,
            highlightthickness=3,
            highlightbackground=COLOR_BROWN_DARK,
        )
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor="center")

        # --- Timer ---
        self.timer_screen = TimerScreen(self.overlay_frame)
        self.timer_screen.pack(pady=(8, 4), padx=20)

        # --- Card grid ---
        self.card_screen = CardScreen(
            self.overlay_frame,
            self.back_img,
            self.front_imgs,
            self.mode,
            self.record_manager,
            self.timer_screen,
            app=self.app,
        )
        self.card_screen.pack(padx=20, pady=(4, 8))

        # --- Pause button ---
        self.pause_button = tk.Button(
            self.overlay_frame,
            text="Pause",
            font=("Arial", 13, "bold"),
            width=12,
            bg=COLOR_BROWN_BUTTON,
            fg="white",
            activebackground=COLOR_BROWN_BUTTON_ACTIVE,
            activeforeground="white",
            bd=2,
            relief="solid",
            cursor="hand2",
            command=self._pause_game,
        )
        self.pause_button.pack(pady=(4, 12), ipady=2)

        self.pack(fill="both", expand=True)
        _logger.info("Game screen initialised — mode='%s'.", self.mode)

    # ------------------------------------------------------------------
    # Pause lifecycle
    # ------------------------------------------------------------------

    def _pause_game(self) -> None:
        """Freeze the timer, disable the cards, and show the pause overlay."""
        if self.pause_overlay is not None:
            return  # Already paused.

        _logger.info("Game paused.")
        self.timer_screen.stop()
        self.card_screen.set_paused(True)
        self.pause_button.config(state=tk.DISABLED)

        self.pause_overlay = PauseOverlay(
            self,
            self.timer_screen,
            self.card_screen,
            resume_callback=self._resume_game,
            replay_callback=self._replay_game,
            back_callback=self._back_to_menu,
        )
        self.pause_overlay.place(
            relx=0.5, rely=0.5, anchor="center", width=300, height=250
        )

    def _resume_game(self) -> None:
        """
        Dismiss the pause overlay and resume the timer and card interaction.

        The timer's :attr:`start_time` is recalculated so that the
        elapsed time displayed is continuous (i.e. the pause duration is
        not counted).
        """
        if self.pause_overlay is not None:
            self.pause_overlay.place_forget()
            self.pause_overlay.destroy()
            self.pause_overlay = None

        self.pause_button.config(state=tk.NORMAL)

        # Recalculate start_time so elapsed time stays correct.
        elapsed = self._get_elapsed_seconds()
        self.timer_screen.start_time = time.time() - elapsed
        self.timer_screen.running = True
        self.timer_screen._tick()
        self.card_screen.set_paused(False)
        _logger.info("Game resumed.")

    def _replay_game(self) -> None:
        """Destroy the pause overlay and restart the game."""
        self._destroy_pause_overlay()
        _logger.info("Replaying game.")
        if self.app is not None:
            self.app.start_game()
        else:
            _logger.warning("No app reference — cannot replay.")

    def _back_to_menu(self) -> None:
        """Destroy the pause overlay and return to the main menu."""
        self._destroy_pause_overlay()
        _logger.info("Returning to main menu.")
        if self.app is not None:
            self.app.show_home()
        else:
            _logger.warning("No app reference — cannot navigate to main menu.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _destroy_pause_overlay(self) -> None:
        """Safely destroy the pause overlay if it exists."""
        if self.pause_overlay is not None:
            self.pause_overlay.destroy()
            self.pause_overlay = None

    def _get_elapsed_seconds(self) -> int:
        """
        Parse the timer label text and return elapsed seconds.

        Returns:
            The number of seconds displayed on the timer label.
        """
        try:
            text: str = self.timer_screen.timer_label.cget("text")
            # Expected format: "Time: MM:SS"
            time_part = text.split("Time: ", maxsplit=1)[-1]
            mins, secs = map(int, time_part.split(":"))
            return mins * 60 + secs
        except (ValueError, IndexError) as exc:
            _logger.error(
                "Could not parse timer label text '%s': %s. Returning 0.",
                text,
                exc,
            )
            return 0
