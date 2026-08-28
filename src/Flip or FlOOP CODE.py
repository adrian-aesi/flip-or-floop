"""
Flip or FlOOP — Animals Edition 🦁

A jungle-themed memory card-matching game built with Tkinter and Pillow.

This module defines :class:`FlipOrFloopApp`, the top-level application
controller that manages screen navigation (home → game → victory → about)
and owns shared resources like the :class:`~record_manager.RecordManager`
and background music.

Run this file directly to launch the game::

    python "Flip or FlOOP CODE.py"
"""

import sys
import tkinter as tk
from PIL import Image, ImageTk

from utils import (
    get_asset_path,
    setup_logger,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_SIZE,
    COLOR_PARCHMENT,
    COLOR_BROWN_DARK,
    COLOR_BROWN_BUTTON,
    COLOR_BROWN_BUTTON_ACTIVE,
    COLOR_TAN_BUTTON,
    COLOR_TAN_BUTTON_ACTIVE,
    COLOR_TEXT_MUTED,
)
from music_player import MusicPlayer
from record_manager import RecordManager
from about_screen import AboutScreen
from victory_screen import VictoryScreen
from game_screen import GameScreen

_logger = setup_logger("app")


class FlipOrFloopApp:
    """
    Main application controller for Flip or FlOOP.

    Responsibilities:

    * Creates and configures the root Tk window.
    * Starts background music and ensures it stops on exit.
    * Manages screen transitions between the **Home**, **Game**,
      **Victory**, and **About** screens by destroying and rebuilding
      widgets as needed.
    * Owns the shared :class:`RecordManager` instance.

    Args:
        root: The root :class:`tk.Tk` window.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Flip or flOOP")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # Start background music.
        MusicPlayer.play("music.mp3")

        # Ensure music stops cleanly when the window is closed.
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Shared state
        self.record_manager = RecordManager()
        self.selected_mode = tk.StringVar(value="easy")
        self.current_mode: str = "easy"

        _logger.info("Application initialised.")
        self.show_home()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_closing(self) -> None:
        """Handle the window-close event: stop music and destroy the window."""
        _logger.info("Application closing.")
        MusicPlayer.stop()
        self.root.destroy()

    # ------------------------------------------------------------------
    # Screen: Home
    # ------------------------------------------------------------------

    def show_home(self) -> None:
        """
        Build and display the **Home** screen.

        Clears all existing widgets, then renders the background image,
        a parchment overlay with the game title, the "Animals Edition"
        badge, difficulty radio buttons, and the *Play* and *About*
        action buttons.
        """
        self._clear_screen()
        _logger.info("Showing home screen.")

        # --- Background image ---
        try:
            self.bg_image = Image.open(get_asset_path("background.png")).resize(WINDOW_SIZE)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except (FileNotFoundError, OSError) as exc:
            _logger.error("Could not load background image: %s", exc)
            self.root.configure(bg=COLOR_PARCHMENT)

        # --- Parchment overlay container ---
        # Offset left (relx=0.45) so it doesn't cover the lion on the
        # bottom-right of the background.
        self.container = tk.Frame(
            self.root,
            bg=COLOR_PARCHMENT,
            highlightthickness=3,
            highlightbackground=COLOR_BROWN_DARK,
        )
        self.container.place(
            relx=0.45, rely=0.5, anchor="center", width=420, height=620
        )

        # --- Title ---
        tk.Label(
            self.container,
            text="flip or flOOP",
            font=("Arial", 34, "bold"),
            bg=COLOR_PARCHMENT,
            fg=COLOR_BROWN_DARK,
        ).pack(pady=(24, 6))

        # --- Animals Edition badge ---
        try:
            animal_img = Image.open(get_asset_path("animals_edition.jpg")).resize((180, 90))
            self.animal_photo = ImageTk.PhotoImage(animal_img)
            tk.Label(
                self.container,
                image=self.animal_photo,
                bd=3,
                relief="solid",
            ).pack(pady=(0, 18))
        except (FileNotFoundError, OSError) as exc:
            _logger.warning("Could not load animals-edition badge: %s", exc)

        # --- Difficulty selection ---
        modes: list[tuple[str, str, str]] = [
            ("flipling mode (4x4 cards)", "easy", "New players, fresh claws! 🐈🐾"),
            ("Wild Mind Maze (6x6 cards)", "hard", "It's a jungle in here! 🦁👑"),
        ]

        for text, mode, subtext in modes:
            frame = tk.Frame(self.container, bg=COLOR_PARCHMENT)
            frame.pack(anchor="w", padx=28, pady=(4, 0))

            tk.Radiobutton(
                frame,
                variable=self.selected_mode,
                value=mode,
                bg=COLOR_PARCHMENT,
                fg=COLOR_BROWN_DARK,
                activebackground=COLOR_PARCHMENT,
            ).pack(side="left")

            tk.Label(
                frame,
                text=text,
                font=("Arial", 14, "bold"),
                bg=COLOR_PARCHMENT,
                fg=COLOR_BROWN_DARK,
            ).pack(side="left")

            tk.Label(
                self.container,
                text=subtext,
                font=("Arial", 10),
                bg=COLOR_PARCHMENT,
                fg=COLOR_TEXT_MUTED,
            ).pack(anchor="w", padx=52, pady=(0, 8))

        # Spacer
        tk.Frame(self.container, bg=COLOR_PARCHMENT, height=8).pack()

        # --- PLAY button ---
        tk.Button(
            self.container,
            text="PLAY",
            font=("Arial", 17, "bold"),
            width=18,
            bg=COLOR_BROWN_BUTTON,
            fg="white",
            activebackground=COLOR_BROWN_BUTTON_ACTIVE,
            activeforeground="white",
            command=self.start_game,
            bd=3,
            relief="solid",
            cursor="hand2",
        ).pack(pady=(8, 8), ipady=6)

        # --- About button ---
        tk.Button(
            self.container,
            text="About",
            font=("Arial", 14, "bold"),
            bg=COLOR_TAN_BUTTON,
            fg="white",
            activebackground=COLOR_TAN_BUTTON_ACTIVE,
            activeforeground="white",
            command=self.show_about,
            bd=3,
            relief="solid",
            width=18,
            cursor="hand2",
        ).pack(pady=(2, 8), ipady=3)

    # ------------------------------------------------------------------
    # Screen: Game
    # ------------------------------------------------------------------

    def start_game(self) -> None:
        """
        Clear the current screen and launch a new game.

        Uses the difficulty mode currently selected via the home screen
        radio buttons.
        """
        self._clear_screen()

        mode: str = self.selected_mode.get()
        self.current_mode = mode
        _logger.info("Starting game — mode='%s'.", mode)

        try:
            back_img = get_asset_path("jungle_ahh.jpg")
            front_imgs = [get_asset_path(f"img{i}.png") for i in range(1, 19)]
        except FileNotFoundError as exc:
            _logger.error("Missing game assets: %s", exc)
            self.show_home()
            return

        try:
            game = GameScreen(
                self.root,
                self.record_manager,
                back_img,
                front_imgs,
                mode=mode,
                app=self,
            )
            game.pack(fill="both", expand=True)
        except (FileNotFoundError, ValueError, OSError) as exc:
            _logger.error("Failed to create game screen: %s", exc)
            self.show_home()

    # ------------------------------------------------------------------
    # Screen: About
    # ------------------------------------------------------------------

    def show_about(self) -> None:
        """Clear the current screen and show the About / Credits page."""
        self._clear_screen()
        _logger.info("Showing about screen.")

        about = AboutScreen(self.root, self.record_manager, self.show_home)
        about.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Screen: Victory
    # ------------------------------------------------------------------

    def show_victory(self, time_str: str, mode: str) -> None:
        """
        Clear the current screen and show the Victory page.

        Args:
            time_str: The player's completion time (``"MM:SS"``).
            mode:     The difficulty mode that was completed.
        """
        self._clear_screen()
        _logger.info("Showing victory screen — time='%s', mode='%s'.", time_str, mode)

        victory = VictoryScreen(
            self.root,
            time_str,
            mode,
            replay_callback=self.start_game,
            back_callback=self.show_home,
        )
        victory.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clear_screen(self) -> None:
        """Destroy all child widgets of the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FlipOrFloopApp(root)
        root.mainloop()
    except Exception:
        _logger.exception("Unhandled exception — the application will now exit.")
        sys.exit(1)