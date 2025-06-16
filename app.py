import tkinter as tk
from tkinter import filedialog
import threading
import os
import pygame
from gestures import start_gesture_loop
from player import MusicPlayer
import time
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

class ConductifyGUI:
    def __init__(self, master):
        self.master = master
        master.title("Conductify - Gesture Music Controller")
        master.geometry("400x400")
        master.configure(bg="#1e1e1e")

        self.player = MusicPlayer()
        self.music_file = None
        self.current_play_time = 0
        self.is_playing = False
        self.last_update_time = time.time()
        self.seeking = False
        self.seek_position = 0

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

        self.progress_canvas = tk.Canvas(master, width=300, height=20, bg="#333333", highlightthickness=0)
        self.progress_canvas.pack(pady=10)
        self.progress_canvas.bind("<Button-1>", self.start_seek)
        self.progress_canvas.bind("<B1-Motion>", self.drag_seek)
        self.progress_canvas.bind("<ButtonRelease-1>", self.end_seek)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="#1DB954")

        # Progress Bar
        self.progress_label = tk.Label(master, text="00:00 / 00:00", fg="white", bg="#1e1e1e", font=("Helvetica", 10))
        self.progress_label.pack(pady=5)

        self.volume_canvas = tk.Canvas(master, width=300, height=10, bg="#333333", highlightthickness=0)
        self.volume_canvas.pack(pady=5)
        self.volume_bar = self.volume_canvas.create_rectangle(0, 0, 150, 10, fill="#1DB954")

        self.total_duration = 0
        self.update_progress()


    def load_music(self):
        self.music_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if self.music_file:
            filename = os.path.basename(self.music_file)
            self.player.load(self.music_file)
            self.total_duration = self.get_audio_length(self.music_file)
            self.status_label.config(text=f"Loaded: {filename}")

    def get_audio_length(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".mp3":
            return int(MP3(filepath).info.length)
        elif ext == ".wav":
            return int(WAVE(filepath).info.length)
        return 0
    
    def update_progress(self):
        if self.music_file:
            if self.is_playing:
                now = time.time()
                elapsed = now - self.last_update_time
                self.current_play_time += elapsed
                progress_width = 300
                progress_ratio = min(self.current_play_time / self.total_duration, 1.0) if self.total_duration > 0 else 0
                bar_length = int(progress_width * progress_ratio)
                self.progress_canvas.coords(self.progress_bar, 0, 0, bar_length, 20)
                self.last_update_time = now

            current_time_str = time.strftime('%M:%S', time.gmtime(self.current_play_time))
            total_time_str = time.strftime('%M:%S', time.gmtime(self.total_duration))
            self.progress_label.config(text=f"{current_time_str} / {total_time_str}")

            if self.current_play_time >= self.total_duration:
                self.current_play_time = 0
                self.is_playing = False
        else:
            self.progress_label.config(text="00:00 / 00:00")
            
        self.master.after(1000, self.update_progress)

    def start_seek(self, event):
        self.seeking = True
        self.update_seek_position(event.x)

    def drag_seek(self, event):
        if self.seeking:
            self.update_seek_position(event.x)

    def end_seek(self, event):
        if self.seeking:
            self.seeking = False
            if self.music_file and self.total_duration > 0:
                seek_time = self.seek_position * self.total_duration
                self.player.play(start=seek_time)
                self.current_play_time = seek_time
                self.last_update_time = time.time()
                self.status_label.config(text=f"Seeked to {int(seek_time)}s")

    def update_seek_position(self, x):
        canvas_width = self.progress_canvas.winfo_width()
        self.seek_position = max(0.0, min(x / canvas_width, 1.0))
        bar_length = int(canvas_width * self.seek_position)
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_length, 20)

    def update_volume_bar(self, volume):
        bar_length = int(volume * 300)
        color = "1DB954" if volume > 0 else "#ff4d4d"
        self.volume_canvas.coords(self.volume_bar, 0, 0, bar_length, 10)
        self.volume_canvas.itemconfig(self.volume_bar, fill=color) 

    def play_music(self):
        self.player.play()
        self.is_playing = True
        self.last_update_time = time.time()
        self.status_label.config(text="Playing...")

    def pause_music(self):
        self.player.pause()
        self.is_playing = False
        self.status_label.config(text="Paused")

    def resume_music(self):
        self.player.resume()
        self.is_playing = True
        self.last_update_time = time.time()
        self.status_label.config(text="Resumed")

    def stop_music(self):
        self.player.stop()
        self.is_playing = False
        self.current_play_time = 0
        self.status_label.config(text="Stopped")

    def start_gesture_detection(self):
        self.status_label.config(text="Starting gesture detection...")
        threading.Thread(target=start_gesture_loop, args=(self.update_status, self.player), daemon=True).start()

    def update_status(self, msg):
        self.status_label.config(text=f"Gesture: {msg}")

        if "Volume" in msg:
            percent = int(''.join(filter(str.isdigit, msg)))
            self.update_volume_bar(percent / 100)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConductifyGUI(root)
    root.mainloop()
