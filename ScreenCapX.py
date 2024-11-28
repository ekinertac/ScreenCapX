import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import rumps
from PIL import Image
from pynput import keyboard
from Quartz import NSData, NSPasteboard, NSPasteboardTypePNG

CONFIG_DIR = Path.home() / ".config"
CONFIG_FILE = CONFIG_DIR / "screenshot_app_config.json"


class ScreenshotApp(rumps.App):
    def __init__(self):
        super(ScreenshotApp, self).__init__("Screenshot App")
        self.menu = [
            "Full Screen",
            "Selected Region",
            None,
            "Set Output Folder...",
            None,
        ]
        self.screenshot_folder = self.load_config()
        self.ensure_screenshot_folder()
        self.modifier_keys = {"cmd": False, "shift": False}  # Track modifier key states
        self.setup_shortcuts()

    def ensure_screenshot_folder(self):
        """Create the Screenshots folder if it doesn't exist."""
        try:
            if not self.screenshot_folder.exists():
                self.screenshot_folder.mkdir(parents=True, exist_ok=True)
                self.show_notification(
                    "Folder Created",
                    f"Screenshots folder created at {self.screenshot_folder}",
                )
        except Exception as e:
            self.show_notification("Error", f"Failed to create folder: {e}")

    def capture(self, mode):
        """Capture a screenshot, optimize the image, and copy it to the clipboard."""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        raw_filename = self.screenshot_folder / f"Screenshot-{timestamp}.png"

        try:
            # Capture the screenshot
            if mode == "Full Screen":
                subprocess.run(["screencapture", "-x", str(raw_filename)])
            elif mode == "Selected Region":
                subprocess.run(["screencapture", "-i", "-x", str(raw_filename)])

            # Check if the file was created (e.g., canceled screenshot with Esc)
            if not raw_filename.exists():
                return

            # Optimize the screenshot
            self.optimize_image(raw_filename)

            # Copy the optimized image to the clipboard
            self.copy_to_clipboard(raw_filename)

        except Exception as e:
            self.show_notification("Error", f"Failed to capture screenshot: {e}")

    def optimize_image(self, input_path):
        """Optimize the image to reduce file size."""
        try:
            with Image.open(input_path) as img:
                img.save(input_path, format="PNG", optimize=True)
        except FileNotFoundError:
            return
        except Exception as e:
            self.show_notification("Error", f"Failed to optimize image: {e}")

    def copy_to_clipboard(self, image_path):
        """Copy the image to the macOS clipboard."""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            with open(image_path, "rb") as img_file:
                img_data = NSData.dataWithContentsOfFile_(str(image_path))
                pasteboard.setData_forType_(img_data, NSPasteboardTypePNG)
                self.play_screenshot_sound()
        except Exception as e:
            self.show_notification("Error", f"Failed to copy image to clipboard: {e}")

    def play_screenshot_sound(self):
        """Play the default macOS screenshot sound."""
        try:
            subprocess.run(
                [
                    "afplay",
                    "/System/Library/Components/CoreAudio.component/Contents/SharedSupport/SystemSounds/system/Screen Capture.aif",
                ],
                check=True,
            )
        except Exception as e:
            print(f"Failed to play screenshot sound: {e}")

    def setup_shortcuts(self):
        """Set up global keyboard shortcuts."""

        def on_press(key):
            try:
                # Track modifier keys
                if key == keyboard.Key.cmd:
                    self.modifier_keys["cmd"] = True
                elif key == keyboard.Key.shift:
                    self.modifier_keys["shift"] = True

                # Check for shortcuts
                if isinstance(key, keyboard.KeyCode) and key.char == "3":
                    if self.modifier_keys["cmd"] and self.modifier_keys["shift"]:
                        self.capture("Full Screen")
                elif isinstance(key, keyboard.KeyCode) and key.char == "4":
                    if self.modifier_keys["cmd"] and self.modifier_keys["shift"]:
                        self.capture("Selected Region")
            except Exception as e:
                self.show_notification("Error", f"Failed to process shortcut: {e}")

        def on_release(key):
            # Reset modifier key states when released
            if key == keyboard.Key.cmd:
                self.modifier_keys["cmd"] = False
            elif key == keyboard.Key.shift:
                self.modifier_keys["shift"] = False

        # Start the keyboard listener
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener_thread = threading.Thread(target=listener.start)
        listener_thread.daemon = True
        listener_thread.start()

    def load_config(self):
        """Load the configuration file for the output folder."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as config_file:
                    config = json.load(config_file)
                return Path(config.get("output_folder", Path.home() / "Screenshots"))
        except Exception as e:
            self.show_notification("Error", f"Failed to load config: {e}")
        return Path.home() / "Screenshots"

    def save_config(self):
        """Save the current output folder to the configuration file."""
        try:
            CONFIG_DIR.mkdir(
                parents=True, exist_ok=True
            )  # Ensure the .config directory exists
            with open(CONFIG_FILE, "w") as config_file:
                json.dump({"output_folder": str(self.screenshot_folder)}, config_file)
        except Exception as e:
            self.show_notification("Error", f"Failed to save configuration: {e}")

    def show_notification(self, title, message):
        """Show a notification, ensuring it runs on the main thread."""
        rumps.notification(title, "", message)

    @rumps.clicked("Full Screen")
    def full_screen(self, _):
        self.capture("Full Screen")

    @rumps.clicked("Selected Region")
    def selected_region(self, _):
        self.capture("Selected Region")

    @rumps.clicked("Set Output Folder...")
    def set_output_folder(self, _):
        """Allow the user to set the output folder dynamically."""
        folder = rumps.Window(
            message="Enter the path to the folder where screenshots will be saved:",
            title="Set Output Folder",
            default_text=str(self.screenshot_folder),
            ok="Set",
            cancel="Cancel",
        ).run()

        if folder.clicked and folder.text.strip():
            new_folder = Path(folder.text.strip())
            try:
                new_folder.mkdir(parents=True, exist_ok=True)
                self.screenshot_folder = new_folder
                self.save_config()
                self.show_notification(
                    "Output Folder Set",
                    f"Screenshots will now be saved to {new_folder}",
                )
            except Exception as e:
                self.show_notification("Error", f"Failed to set output folder: {e}")


if __name__ == "__main__":
    ScreenshotApp().run()
