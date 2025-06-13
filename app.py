import tkinter as tk
from tkinter import filedialog
import threading
import os
from gestures import start_gesture_loop
from player import MusicPlayer

class ConductifyGUI:
    def __init__(self, master):
        self.master = master
        master.title("Conductify - Gesture Music Controller")
        master.geometry("400x400")
        master.configure(bg="#1e1e1e")

        self.player = MusicPlayer()
        self.music_file = None

        # Title
        self.title_label = tk.Label(master, text="🎶 Conductify", fg="white", bg="#1e1e1e", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=20)

        # Load Music
        self.load_button = tk.Button(master, text="🎵 Load Music", command=self.load_music)
        self.load_button.pack(pady=5)

        # Controls
        self.play_button = tk.Button(master, text="▶️ Play", command=self.play_music)
        self.play_button.pack(pady=5)

        self.pause_button = tk.Button(master, text="⏸️ Pause", command=self.pause_music)
        self.pause_button.pack(pady=5)

        self.resume_button = tk.Button(master, text="🔁 Resume", command=self.resume_music)
        self.resume_button.pack(pady=5)

        self.stop_button = tk.Button(master, text="⏹️ Stop", command=self.stop_music)
        self.stop_button.pack(pady=5)

        # Gesture Control
        self.gesture_button = tk.Button(master, text="🖐️ Start Gesture Detection", command=self.start_gesture_detection)
        self.gesture_button.pack(pady=10)

        # Status
        self.status_label = tk.Label(master, text="", fg="white", bg="#1e1e1e", font=("Helvetica", 12))
        self.status_label.pack(pady=20)

    def load_music(self):
        self.music_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if self.music_file:
            filename = os.path.basename(self.music_file)
            self.player.load(self.music_file)
            self.status_label.config(text=f"Loaded: {filename}")

    def play_music(self):
        self.player.play()
        self.status_label.config(text="Playing...")

    def pause_music(self):
        self.player.pause()
        self.status_label.config(text="Paused")

    def resume_music(self):
        self.player.resume()
        self.status_label.config(text="Resumed")

    def stop_music(self):
        self.player.stop()
        self.status_label.config(text="Stopped")

    def start_gesture_detection(self):
        self.status_label.config(text="Starting gesture detection...")
        threading.Thread(target=start_gesture_loop, args=(self.update_status, self.player), daemon=True).start()

    def update_status(self, msg):
        self.status_label.config(text=f"Gesture: {msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConductifyGUI(root)
    root.mainloop()
