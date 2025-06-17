import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import pygame
from gestures import start_gesture_loop
from player import MusicPlayer
import time
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from pathlib import Path

class ConductifyGUI:
    def __init__(self, master):
        self.master = master
        master.title("Conductify - Advanced Gesture Music Controller")
        master.geometry("600x700")
        master.configure(bg="#1a1a1a")
        master.resizable(False, False)
        
        self.player = MusicPlayer()
        self.music_file = None
        self.current_play_time = 0
        self.is_playing = False
        self.last_update_time = time.time()
        self.seeking = False
        self.seek_position = 0
        self.gesture_active = False
        self.total_duration = 0
        self.playlist = []
        self.current_track_index = 0
        self.gesture_thread = None
        self.update_thread_active = True
        
        self.setup_ui()
        self.update_progress()
        
        # Bind window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        # Title with enhanced styling
        title_frame = tk.Frame(self.master, bg="#1a1a1a")
        title_frame.pack(pady=10)
        
        self.title_label = tk.Label(title_frame, text="🎼 Conductify Pro", 
                                   fg="#00ff88", bg="#1a1a1a", 
                                   font=("Helvetica", 24, "bold"))
        self.title_label.pack()
        
        self.subtitle_label = tk.Label(title_frame, text="Advanced Gesture Music Control", 
                                      fg="#888888", bg="#1a1a1a", 
                                      font=("Helvetica", 12))
        self.subtitle_label.pack()
        
        # File Management Section
        file_frame = tk.LabelFrame(self.master, text="Music Library", 
                                  fg="white", bg="#2d2d2d", 
                                  font=("Helvetica", 12, "bold"))
        file_frame.pack(pady=10, padx=20, fill="x")
        
        button_style = {
            "bg": "#4a4a4a", 
            "fg": "white", 
            "font": ("Helvetica", 10),
            "relief": "flat",
            "padx": 10,
            "pady": 5
        }
        
        self.load_button = tk.Button(file_frame, text="🎵 Load Single Track", 
                                   command=self.load_music, **button_style)
        self.load_button.pack(pady=5, fill="x")
        
        self.load_folder_button = tk.Button(file_frame, text="📁 Load Folder", 
                                          command=self.load_folder, **button_style)
        self.load_folder_button.pack(pady=5, fill="x")
        
        # Current Track Info
        info_frame = tk.LabelFrame(self.master, text="Now Playing", 
                                  fg="white", bg="#2d2d2d", 
                                  font=("Helvetica", 12, "bold"))
        info_frame.pack(pady=10, padx=20, fill="x")
        
        self.track_label = tk.Label(info_frame, text="No track loaded", 
                                   fg="#00ff88", bg="#2d2d2d", 
                                   font=("Helvetica", 11), wraplength=450)
        self.track_label.pack(pady=5)
        
        self.time_label = tk.Label(info_frame, text="00:00 / 00:00", 
                                  fg="#888888", bg="#2d2d2d", 
                                  font=("Helvetica", 10))
        self.time_label.pack(pady=2)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(info_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.bind("<Button-1>", self.seek_music)
        
        # Playback Controls
        controls_frame = tk.LabelFrame(self.master, text="Playback Controls", 
                                      fg="white", bg="#2d2d2d", 
                                      font=("Helvetica", 12, "bold"))
        controls_frame.pack(pady=10, padx=20, fill="x")
        
        button_frame = tk.Frame(controls_frame, bg="#2d2d2d")
        button_frame.pack(pady=10)
        
        control_button_style = {
            "bg": "#555555", 
            "fg": "white", 
            "font": ("Helvetica", 12),
            "relief": "raised",
            "padx": 15,
            "pady": 8,
            "width": 8
        }
        
        self.prev_button = tk.Button(button_frame, text="⏮️ Prev", 
                                   command=self.previous_track, **control_button_style)
        self.prev_button.grid(row=0, column=0, padx=5)
        
        self.play_button = tk.Button(button_frame, text="▶️ Play", 
                                   command=self.toggle_play, **control_button_style)
        self.play_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="⏹️ Stop", 
                                   command=self.stop_music, **control_button_style)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        self.next_button = tk.Button(button_frame, text="⏭️ Next", 
                                   command=self.next_track, **control_button_style)
        self.next_button.grid(row=0, column=3, padx=5)
        
        # Volume and Tempo Controls
        volume_frame = tk.Frame(controls_frame, bg="#2d2d2d")
        volume_frame.pack(pady=10, fill="x")
        
        tk.Label(volume_frame, text="Volume:", fg="white", bg="#2d2d2d", 
                font=("Helvetica", 10)).pack(side="left", padx=(10, 5))
        
        self.volume_var = tk.DoubleVar(value=50)
        self.volume_scale = tk.Scale(volume_frame, from_=0, to=100, orient="horizontal", 
                                   variable=self.volume_var, command=self.set_volume,
                                   bg="#2d2d2d", fg="white", length=200)
        self.volume_scale.pack(side="left", padx=5)
        
        self.volume_label = tk.Label(volume_frame, text="50%", fg="#00ff88", bg="#2d2d2d", 
                                   font=("Helvetica", 10))
        self.volume_label.pack(side="left", padx=5)
        
        # Gesture Control Section
        gesture_frame = tk.LabelFrame(self.master, text="Gesture Control", 
                                     fg="white", bg="#2d2d2d", 
                                     font=("Helvetica", 12, "bold"))
        gesture_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.gesture_button = tk.Button(gesture_frame, text="🤚 Start Gesture Control", 
                                      command=self.toggle_gesture_control, **button_style)
        self.gesture_button.pack(pady=10)
        
        # Gesture Status
        self.gesture_status_label = tk.Label(gesture_frame, text="Gesture control inactive", 
                                           fg="#888888", bg="#2d2d2d", 
                                           font=("Helvetica", 10))
        self.gesture_status_label.pack(pady=5)
        
        # Gesture Instructions
        instructions_text = """Gesture Controls:
• Swipe Up: Increase Volume (Crescendo)
• Swipe Down: Decrease Volume (Diminuendo)
• Circle Clockwise: Speed Up Tempo
• Circle Counter-clockwise: Slow Down Tempo
• Hold Still: Pause/Resume
• Swipe Left: Previous Track
• Swipe Right: Next Track"""
        
        self.instructions_label = tk.Label(gesture_frame, text=instructions_text, 
                                         fg="#cccccc", bg="#2d2d2d", 
                                         font=("Helvetica", 9), justify="left")
        self.instructions_label.pack(pady=10, padx=10, anchor="w")
        
        # Playlist Section
        playlist_frame = tk.LabelFrame(self.master, text="Playlist", 
                                      fg="white", bg="#2d2d2d", 
                                      font=("Helvetica", 12, "bold"))
        playlist_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Playlist with scrollbar
        playlist_container = tk.Frame(playlist_frame, bg="#2d2d2d")
        playlist_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.playlist_listbox = tk.Listbox(playlist_container, bg="#3d3d3d", fg="white", 
                                         selectbackground="#00ff88", font=("Helvetica", 9))
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        
        playlist_scrollbar = tk.Scrollbar(playlist_container, command=self.playlist_listbox.yview)
        playlist_scrollbar.pack(side="right", fill="y")
        self.playlist_listbox.config(yscrollcommand=playlist_scrollbar.set)
        
        self.playlist_listbox.bind("<Double-Button-1>", self.play_selected_track)
        
        # Status Bar
        self.status_label = tk.Label(self.master, text="Ready", fg="#00ff88", bg="#1a1a1a", 
                                   font=("Helvetica", 10), anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=20, pady=5)
    
    def load_music(self):
        """Load a single music file"""
        file_types = [
            ("Audio files", "*.mp3 *.wav *.ogg *.m4a *.flac"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(title="Select Music File", filetypes=file_types)
        if file_path:
            if self.player.load(file_path):
                self.music_file = file_path
                self.playlist = [file_path]
                self.current_track_index = 0
                self.update_track_info()
                self.update_playlist_display()
                self.get_track_duration()
                self.status_update(f"Loaded: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Could not load the selected file")
    
    def load_folder(self):
        """Load all music files from a folder"""
        folder_path = filedialog.askdirectory(title="Select Music Folder")
        if folder_path:
            if self.player.load_folder(folder_path):
                self.playlist = self.player.playlist
                self.current_track_index = 0
                self.music_file = self.playlist[0] if self.playlist else None
                self.update_track_info()
                self.update_playlist_display()
                self.get_track_duration()
                self.status_update(f"Loaded {len(self.playlist)} tracks from folder")
            else:
                messagebox.showerror("Error", "No audio files found in the selected folder")
    
    def toggle_play(self):
        """Toggle between play and pause"""
        if not self.music_file:
            messagebox.showwarning("Warning", "Please load a music file first")
            return
        
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_button.config(text="▶️ Play")
            self.status_update("Paused")
        else:
            if self.player.play():
                self.is_playing = True
                self.play_button.config(text="⏸️ Pause")
                self.status_update("Playing")
            else:
                messagebox.showerror("Error", "Could not play the file")
    
    def stop_music(self):
        """Stop music playback"""
        self.player.stop()
        self.is_playing = False
        self.current_play_time = 0
        self.play_button.config(text="▶️ Play")
        self.progress_var.set(0)
        self.status_update("Stopped")
    
    def next_track(self):
        """Play next track"""
        if self.playlist and len(self.playlist) > 1:
            was_playing = self.is_playing
            if self.player.next_track():
                self.current_track_index = self.player.current_track_index
                self.music_file = self.player.music_file
                self.update_track_info()
                self.get_track_duration()
                self.playlist_listbox.selection_clear(0, tk.END)
                self.playlist_listbox.selection_set(self.current_track_index)
                if was_playing:
                    self.is_playing = True
                    self.play_button.config(text="⏸️ Pause")
                self.status_update(f"Next: {os.path.basename(self.music_file)}")
    
    def previous_track(self):
        """Play previous track"""
        if self.playlist and len(self.playlist) > 1:
            was_playing = self.is_playing
            if self.player.previous_track():
                self.current_track_index = self.player.current_track_index
                self.music_file = self.player.music_file
                self.update_track_info()
                self.get_track_duration()
                self.playlist_listbox.selection_clear(0, tk.END)
                self.playlist_listbox.selection_set(self.current_track_index)
                if was_playing:
                    self.is_playing = True
                    self.play_button.config(text="⏸️ Pause")
                self.status_update(f"Previous: {os.path.basename(self.music_file)}")
    
    def play_selected_track(self, event):
        """Play selected track from playlist"""
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.playlist):
                self.current_track_index = index
                self.player.current_track_index = index
                self.music_file = self.playlist[index]
                if self.player.load(self.music_file):
                    self.update_track_info()
                    self.get_track_duration()
                    if self.player.play():
                        self.is_playing = True
                        self.play_button.config(text="⏸️ Pause")
                        self.status_update(f"Playing: {os.path.basename(self.music_file)}")
    
    def set_volume(self, volume):
        """Set volume from scale"""
        vol = float(volume) / 100.0
        self.player.set_volume(vol)
        self.volume_label.config(text=f"{int(volume)}%")
    
    def seek_music(self, event):
        """Seek to position in track"""
        if self.total_duration > 0:
            click_x = event.x
            bar_width = self.progress_bar.winfo_width()
            if bar_width > 0:
                position_ratio = click_x / bar_width
                seek_time = position_ratio * self.total_duration
                self.current_play_time = seek_time
                # Note: pygame doesn't support seeking, so this is a placeholder
                self.status_update(f"Seek to {self.format_time(seek_time)}")
    
    def toggle_gesture_control(self):
        """Toggle gesture control on/off"""
        if not self.gesture_active:
            if not self.music_file:
                messagebox.showwarning("Warning", "Please load a music file first")
                return
            
            self.gesture_active = True
            self.gesture_button.config(text="🛑 Stop Gesture Control", bg="#ff4444")
            self.gesture_status_label.config(text="Gesture control ACTIVE - Camera starting...", fg="#00ff88")
            
            # Start gesture recognition in a separate thread
            self.gesture_thread = threading.Thread(target=self.start_gesture_recognition, daemon=True)
            self.gesture_thread.start()
            
        else:
            self.gesture_active = False
            self.gesture_button.config(text="🤚 Start Gesture Control", bg="#4a4a4a")
            self.gesture_status_label.config(text="Gesture control inactive", fg="#888888")
            self.status_update("Gesture control stopped")
    
    def start_gesture_recognition(self):
        """Start gesture recognition loop"""
        try:
            start_gesture_loop(self.gesture_status_update, self.player)
        except Exception as e:
            self.gesture_status_label.config(text=f"Gesture error: {str(e)}", fg="#ff4444")
            self.gesture_active = False
            self.gesture_button.config(text="🤚 Start Gesture Control", bg="#4a4a4a")
    
    def gesture_status_update(self, message):
        """Update gesture status from gesture recognition"""
        def update():
            self.gesture_status_label.config(text=message, fg="#00ff88")
            self.status_update(message)
            # Update volume display if volume changed
            current_volume = int(self.player.get_volume() * 100)
            self.volume_var.set(current_volume)
            self.volume_label.config(text=f"{current_volume}%")
        
        self.master.after(0, update)
    
    def update_track_info(self):
        """Update current track information display"""
        if self.music_file:
            filename = os.path.basename(self.music_file)
            track_info = f"🎵 {filename}"
            if self.playlist and len(self.playlist) > 1:
                track_info += f" ({self.current_track_index + 1}/{len(self.playlist)})"
            self.track_label.config(text=track_info)
        else:
            self.track_label.config(text="No track loaded")
    
    def update_playlist_display(self):
        """Update playlist display"""
        self.playlist_listbox.delete(0, tk.END)
        for i, track in enumerate(self.playlist):
            filename = os.path.basename(track)
            display_text = f"{i+1:2d}. {filename}"
            self.playlist_listbox.insert(tk.END, display_text)
        
        if self.playlist:
            self.playlist_listbox.selection_set(self.current_track_index)
    
    def get_track_duration(self):
        """Get duration of current track"""
        if not self.music_file:
            return
        
        try:
            file_ext = os.path.splitext(self.music_file)[1].lower()
            
            if file_ext == '.mp3':
                audio = MP3(self.music_file)
                self.total_duration = audio.info.length
            elif file_ext == '.wav':
                audio = WAVE(self.music_file)
                self.total_duration = audio.info.length
            elif file_ext == '.flac':
                audio = FLAC(self.music_file)
                self.total_duration = audio.info.length
            elif file_ext == '.m4a':
                audio = MP4(self.music_file)
                self.total_duration = audio.info.length
            else:
                self.total_duration = 0
                
        except Exception as e:
            print(f"Error getting duration: {e}")
            self.total_duration = 0
    
    def update_progress(self):
        """Update progress bar and time display"""
        if not self.update_thread_active:
            return
        
        if self.is_playing and self.total_duration > 0:
            current_time = time.time()
            if not self.seeking:
                time_diff = current_time - self.last_update_time
                self.current_play_time += time_diff
                
                if self.current_play_time >= self.total_duration:
                    # Track finished, play next if available
                    if len(self.playlist) > 1:
                        self.next_track()
                    else:
                        self.stop_music()
                    self.current_play_time = 0
            
            self.last_update_time = current_time
            
            # Update progress bar
            if self.total_duration > 0:
                progress = (self.current_play_time / self.total_duration) * 100
                self.progress_var.set(min(progress, 100))
            
            # Update time display
            current_str = self.format_time(self.current_play_time)
            total_str = self.format_time(self.total_duration)
            self.time_label.config(text=f"{current_str} / {total_str}")
        
        # Schedule next update
        self.master.after(1000, self.update_progress)
    
    def format_time(self, seconds):
        """Format time in MM:SS format"""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def status_update(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
    
    def on_closing(self):
        """Handle window closing"""
        self.update_thread_active = False
        self.gesture_active = False
        if self.player:
            self.player.stop()
            self.player.cleanup()
        self.master.destroy()

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ConductifyGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted")
    finally:
        if hasattr(app, 'player'):
            app.player.cleanup()

if __name__ == "__main__":
    main()