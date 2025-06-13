import tkinter as tk
from tkinter import filedialog
import pygame
from gestures import start_gesture_loop

class ConductifyGUI:
    def __init__(self, master):
        self.master = master
        master.title("Conductify - Gesture Music Controller")
        master.geometry("400x300")
        master.configure(bg="#1e1e1e")

        # Initialize the pygame mixer
        pygame.mixer.init()
        self.music_file = None

        # Title Label
        self.title_label = tk.Label(master, text="Conductify", fg="white", bg="#1e1e1e", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=20)

        # Load Button
        self.load_button = tk.Button(master, text="Load Music", command=self.load_music)
        self.load_button.pack(pady=5)

        # Play button
        self.play_button = tk.Button(master, text="Play", command=self.play_music)
        self.play_button.pack(pady=5)

        # Pause button
        self.pause_button = tk.Button(master, text="Pause", command=self.pause_music)
        self.pause_button.pack(pady=5)

        # Start Getsure Detection Button 
        self.gesture_button = tk.Button(master, text="Start Gesture Detection", command=self.start_gesture_detection)
        self.gesture_button.pack(pady=5)

        # Status Label
        self.status_label = tk.Label(master, text="", fg="white", bg="#1e1e1e")
        self.status_label.pack(pady=10)

    def load_music(self):
        self.music_file = filedialog.askopenfilename(filetypes=[("Audio FIles", "*.mp3 *.wav")])
        if self.music_file:
            self.status_label.config(text=f"Loaded: {self.music_file.split('/')[-1]}")

    def play_music(self):
        if self.music_file:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play()
            self.status_label.config(text="Playing...")
    
    def pause_music(self):
        pygame.mixer.music.pause()
        self.status_label.config(text="Paused")

    def start_gesture_detection(self):
        self.status_label.config(text="Starting gesture detection...")
        start_gesture_loop(self.update_status)
    
    def update_status(self, msg):
        self.status_label.config(text=msg )

if __name__ == "__main__":
    root = tk.Tk()
    app = ConductifyGUI(root)
    root.mainloop()