# Package imports
import os
import random
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

# Module Imports
from player import MusicPlayer
from gestures import start_gesture_loop

# GUI Class
class ConductifyGUI:
    # Class Definition
    def __init__(self, master):
        self.master = master # Initializing main application window
        master.title("Conductify - Gesture Music Controller") # Initializing window title
        master.geometry("800x500") # Initializing window size
        master.configure(bg="#1e1e1e") # Initalizing the background of the window
        master.protocol("WM_DELETE_WINDOW", self.on_closing) # Delete window when closed
        
        # Music State Initializations
        self.playlist = [] # Initializing the playlist 
        self.shuffle_history = []
        self.current_track_index = 0 # Initializing the current track index
        self.music_file = None # Initializing the music_file which stores the address
        self.is_playing = False # Initializing if track is playing
        self.total_duration = 0 # Initializing total duration of the track
        self.current_play_time = 0 # Initializing elapsed track time
        self.last_update_time = time.time() # Initializing the last time track time was updated after seeking
        self.update_thread_active = True # Initialing if thread is updated
        self.seeking = False # Initializing if seeking track
        self.loop_mode = "Off"
        self.shuffle_mode = False

        # Gesture Control Initializations
        self.gesture_active = False # Initializing if gesture mode is active
        self.gesture_thread = None # Initializing thread when gesture mode is active

        # Music Player Instance
        self.player = MusicPlayer() # Initializing the music player

        # UI components
        self.setup_ui()

        # Start Progress Updater
        self.master.after(1000, self.update_progress)

    def setup_ui(self):
        # UI Layout

        # Track Label
        self.track_label = tk.Label(self.master, text="No track loaded", bg="#1e1e1e",
                                    fg="#ffffff", font=("Arial", 14)) # Label which stores song name
        self.track_label.pack(pady=10) # Packing the label

        # Playlist box
        self.playlist_listbox = tk.Listbox(self.master, selectbackground="#4a90e2",
                                           font=("Consolas", 11)) # Playlist box which stores all songs in order
        self.playlist_listbox.pack(pady=5, fill=tk.X, padx=20) # Packing the list box
        self.playlist_listbox.bind("<<ListboxSelect>>", self.play_selected_track) # Binding the listbox to play the selected track from the listbox by clicking on the track

        # Playback buttons
        controls = tk.Frame(self.master, bg="#1e1e1e") # Frame which contains all the playback buttons
        controls.pack(pady=10) # Packing the frame

        tk.Button(controls, text="Previous", command=self.previous_track).grid(row=0, column=0, padx=10) # Button to change to previous song in the playlist
        self.play_button = tk.Button(controls, text="Play", command=self.toggle_playback) # Button to play or pause the loaded song
        self.play_button.grid(row=0, column=1, padx=10) # Packing the button
        tk.Button(controls, text="Next", command=self.next_track).grid(row=0, column=2, padx=10) # Button to change to next song in the playlist
        tk.Button(controls, text="Load", command=self.load_music).grid(row=0, column=3, padx=10) # Button to load track(s) 
        self.loop_button = tk.Button(controls, text="Loop: Off", command=self.toggle_loop_mode)
        self.loop_button.grid(row=0, column=4, padx=10)
        self.shuffle_button = tk.Button(controls, text="Shuffle: Off", command=self.toggle_shuffle_mode)
        self.shuffle_button.grid(row=0, column=5, pady=5)

        # Volume Control
        volume_frame = tk.Frame(self.master, bg="#1e1e1e") # Frame which contains the volume slider
        volume_frame.pack(pady=10) # Packing the frame
        self.volume_var = tk.DoubleVar(value=100) # Max volume set to 100
        self.volume_label = tk.Label(volume_frame, text="100%", fg="#ffffff", bg="#1e1e1e") # Label which displays the volume
        self.volume_label.pack(side=tk.LEFT, padx=5) # Packing the label
        volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var, 
                                 command=self.set_volume, bg="#1e1e1e", fg="#ffffff") # Volume slider which can change the volume
        volume_slider.pack() # Packing the slider

        # Progress Bar
        self.progress_var = tk.DoubleVar() 
        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=700, variable=self.progress_var) 
        self.progress_bar.pack(pady=5) # Packing the progress bar
        self.progress_bar.bind("<Button-1>", self.seek_music) # Binding the progress bar to seek_music function

        # Time Label
        self.time_label = tk.Label(self.master, text="00:00 / 00:00", bg="#1e1e1e", fg="#ffffff") # Label which displays the elapsed time of the song
        self.time_label.pack() # Packing the label

        # Gesture control
        self.gesture_button = tk.Button(self.master, text="Start Gesture Control", bg='#4a4a4a', 
                                        fg="white", command=self.toggle_gesture_control) # Button which starts gesture control
        self.gesture_button.pack(pady=10) # Packing the button

        self.gesture_status_label = tk.Label(self.master, text="Gesture control inactive", fg="#888888", bg="#1e1e1e") # Label which displays the status of gestures
        self.gesture_status_label.pack() # Packing the label

        # Status bar
        self.status_label = tk.Label(self.master, text="", bg="#1e1e1e", fg="#888888", anchor="w") # Label whcih gives the status of the application
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM) # Packing the label

    def load_music(self):
        # Responsible for the loading logic of the app
        files = filedialog.askopenfilenames(
            filetypes=[
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("OGG Files", "*.ogg"),
                ("M4A Files", "*.m4a")
            ]
        ) # Only allowing music files to be loaded to the application

        if files: # Checking if any files exist
            self.playlist = list(files) # Creating a list of those files
            self.current_track_index = 0 
            self.music_file = self.playlist[0] # Setting the music file to be played to the first one in the playlist
            self.player.load_playlist(self.playlist) # Loading the playlist to the app
            if self.player.load_track(0): # Checking if 1st track is loaded
                self.update_playlist_display() # Updating the playlist display to focus on the track playing
                self.update_track_info() # Updating track info like name and duration
                self.get_track_duration() # Getting the track duration
                self.status_update("Loaded track/tracks.") # Updating status
    
    def toggle_playback(self):
        # Toggle between play and pause
        if self.is_playing: # Chekcing if track is playing
            self.player.pause() # Pausing the track
            self.is_playing = False 
            self.play_button.config(text="Play") # Changing text of the button
            self.status_update("Paused") # Updating status
        else:
            if self.player.is_paused: # Checking if track is paused
                self.player.resume() # Resuming the track
            else:
                self.player.play() # Playing the track if not playing or not paused
            self.is_playing = True
            self.play_button.config(text="Pause") # Changing text of the button
            self.last_update_time = time.time() # Changing last update time
            self.status_update(f"Playing: {os.path.basename(self.music_file)}") # Updating status
    
    def next_track(self):
        # Play next track
        if self.playlist and len(self.playlist) > 1:
            was_playing = self.is_playing

            if self.shuffle_mode:
                self.shuffle_history.append(self.current_track_index)
                next_index = random.randint(0, len(self.playlist) - 1)
                while next_index == self.current_track_index:
                    next_index = random.randint(0, len(self.playlist) - 1)
                success = self.player.load_track(next_index)
                if not success:
                    return
                self.current_track_index = next_index
                self.music_file = self.player.playlist[next_index]
            else:
                if not self.player.next_track():
                    return
                self.current_track_index = self.player.current_track_index
                self.music_file = self.player.playlist[self.current_track_index]

            self.update_track_info()
            self.get_track_duration()
            self.playlist_listbox.selection_clear(0, tk.END)
            self.playlist_listbox.selection_set(self.current_track_index)
            self.current_play_time = 0
            self.last_update_time = time.time()
            self.progress_var.set(0)

            if was_playing:
                self.player.play()
                self.is_playing = True
                self.play_button.config(text="Pause")

            self.status_update(f"Next: {os.path.basename(self.music_file)}")

    
    def previous_track(self):
        # Play previous track
        if self.playlist and len(self.playlist) > 1: # Checking if playlist exists and has more than 1 track to change to the previous one
            was_playing = self.is_playing 

            if self.shuffle_mode and self.shuffle_history:
                prev_index = self.shuffle_history.pop()
                success = self.player.load_track(prev_index)
                if not success:
                    return
                self.current_track_index = prev_index
                self.music_file = self.player.playlist[prev_index]
            else:
                if not self.player.previous_track():
                    return
                self.current_track_index = self.player.current_track_index
                self.music_file = self.player.playlist[self.current_track_index]

            self.update_track_info() 
            self.get_track_duration()
            self.playlist_listbox.selection_clear(0, tk.END)
            self.current_play_time = 0
            self.last_update_time = time.time()
            self.playlist_listbox.selection_set(self.current_track_index)
            self.progress_var.set(0)

            if was_playing:
                self.player.play()
                self.is_playing = True
                self.play_button.config(text="Pause")
            self.status_update(f"Previous: {os.path.basename(self.music_file)}")

    def toggle_loop_mode(self):
        if self.loop_mode == "Off":
            self.loop_mode = "One"
            self.loop_button.config(text="Loop: One")
        elif self.loop_mode == "One":
            self.loop_mode = "All"
            self.loop_button.config(text="Loop: All")
        else:
            self.loop_mode = "Off"
            self.loop_button.config(text="Loop: Off")

        self.status_update(f"Loop mode: {self.loop_mode}")

    def toggle_shuffle_mode(self):
        self.shuffle_mode = not self.shuffle_mode
        state = "On" if self.shuffle_mode else "Off"
        self.shuffle_button.config(text=f"Shuffle: {state}")
        self.status_update(f"Shuffle mode set to: {state}")

    def play_selected_track(self, event):
        # Play selected track from playlist
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.playlist):
                self.current_track_index = index
                self.player.current_track_index = index
                self.player.load_playlist(self.playlist)
                self.player.current_track_index = index
                self.music_file = self.music_file = self.playlist[index]
                if self.player.load_track(index):
                    self.current_play_time = 0
                    self.last_update_time = time.time()
                    self.progress_var.set(0)
                    self.update_track_info()
                    self.get_track_duration()
                    if self.player.play():
                        self.is_playing = True
                        self.play_button.config(text="Pause")
                        self.status_update(f"Playing: {os.path.basename(self.music_file)}")
    
    def set_volume(self, volume):
        # Set volume from scale
        vol = float(volume) / 100.0
        self.player.set_volume(vol)
        self.volume_label.config(text=f"{int(volume)}%")
    
    def seek_music(self, event):
        # Seek to position in track
        if self.total_duration > 0:
            click_x = event.x
            bar_width = self.progress_bar.winfo_width()
            if bar_width > 0:
                position_ratio = click_x / bar_width
                seek_time = position_ratio * self.total_duration
                self.current_play_time = seek_time
                self.player.seek(seek_time)
                self.current_play_time = seek_time
                self.last_update_time = time.time()
                self.status_update(f"Seek to {self.format_time(seek_time)}")
    
    def toggle_gesture_control(self):
        # Toggle gesture control on/off
        if not self.gesture_active:
            if not self.music_file:
                messagebox.showwarning("Warning", "Please load a music file first")
                return
            
            self.gesture_active = True
            self.gesture_button.config(text="Stop Gesture Control", bg="#ff4444")
            self.gesture_status_label.config(text="Gesture control ACTIVE - Camera starting...", fg="#00ff88")
            
            # Start gesture recognition in a separate thread
            self.gesture_thread = threading.Thread(target=self.start_gesture_recognition, daemon=True)
            self.gesture_thread.start()
            
        else:
            self.gesture_active = False
            self.gesture_button.config(text="Start Gesture Control", bg="#4a4a4a")
            self.gesture_status_label.config(text="Gesture control inactive", fg="#888888")
            self.status_update("Gesture control stopped")
    
    def start_gesture_recognition(self):
        # Start gesture recognition loop
        try:
            start_gesture_loop(self.gesture_status_update, self.player)
        except Exception as e:
            self.gesture_status_label.config(text=f"Gesture error: {str(e)}", fg="#ff4444")
            self.gesture_active = False
            self.gesture_button.config(text="Start Gesture Control", bg="#4a4a4a")
    
    def gesture_status_update(self, message):
        # Update gesture status from gesture recognition
        def update():
            self.gesture_status_label.config(text=message, fg="#00ff88")
            self.status_update(message)
            # Update volume display if volume changed
            current_volume = int(self.player.get_volume() * 100)
            self.volume_var.set(current_volume)
            self.volume_label.config(text=f"{current_volume}%")
        
        self.master.after(0, update)
    
    def update_track_info(self):
        # Update current track information display
        if self.music_file:
            filename = os.path.basename(self.music_file)
            track_info = f"{filename}"
            if self.playlist and len(self.playlist) > 1:
                track_info += f" ({self.current_track_index + 1}/{len(self.playlist)})"
            self.track_label.config(text=track_info)
        else:
            self.track_label.config(text="No track loaded")
    
    def update_playlist_display(self):
        # Update playlist display
        self.playlist_listbox.delete(0, tk.END)
        for i, track in enumerate(self.playlist):
            filename = os.path.basename(track)
            display_text = f"{i+1:2d}. {filename}"
            self.playlist_listbox.insert(tk.END, display_text)
        
        if self.playlist:
            self.playlist_listbox.selection_set(self.current_track_index)
    
    def get_track_duration(self):
        # Get duration of current track
        if not self.music_file:
            return
        try:
            ext = os.path.splitext(self.music_file)[1].lower()
            if ext == '.mp3':
                audio = MP3(self.music_file)
            elif ext == '.wav':
                audio = WAVE(self.music_file)
            elif ext == '.flac':
                audio = FLAC(self.music_file)
            elif ext == '.m4a':
                audio = MP4(self.music_file)
            else:
                audio = None
            self.total_duration = audio.info.length if audio else 0
        except Exception as e:
            print(f"Error getting duration: {e}")
            self.total_duration = 0
    
    def update_progress(self):
        # Update progress bar and time display
        if not self.update_thread_active:
            return
        
        if self.is_playing and self.total_duration > 0:
            current_time = time.time()
            if not self.seeking:
                time_diff = current_time - self.last_update_time
                self.current_play_time += time_diff
                
                if self.current_play_time >= self.total_duration:
                    if self.loop_mode == "One":
                        self.current_play_time = 0
                        self.player.seek(0)
                        self.last_update_time = time.time()
                        self.status_update("Replaying track (Loop One)")
                    elif self.loop_mode == "All":
                        self.next_track()
                    else:
                        # Loop off
                        if len(self.playlist) > 1 and self.current_track_index < len(self.playlist) - 1:
                            self.next_track()
                        else:
                            self.player.stop()
                            self.is_playing = False
                            self.play_button.config(text="Play")
                            self.status_update("Playback finished")
            
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
        # Format time in MM:SS format 
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def status_update(self, message):
        # Update status bar
        self.status_label.config(text=message)
    
    def on_closing(self):
        # Handle window closing
        self.update_thread_active = False
        self.gesture_active = False
        if self.player:
            self.player.stop()
            self.player.cleanup()
        self.master.destroy()

def main():
    # Main function to run the application
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