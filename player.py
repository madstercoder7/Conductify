# Import
import pygame
import os
import random
from pathlib import Path

# Music Player class 
class MusicPlayer:
    def __init__(self):
        # Class definition
        pygame.mixer.init() # Initializing the pygame mixer
        self.playlist = [] # Initializing the playlist
        self.current_track_index = 0 # Initializing the current track index
        self.volume = 0.5   # Initializing the initial volume
        self.is_playing = False # Initializing whether track is playing
        self.is_paused = False # Initializing whether track is paused
        self.music_file = None

    def load_playlist(self, file_paths):
        # Load multiple files as a playlist
        if isinstance(file_paths, (str, Path)): # Checks if path is a single string to load only one track
            file_paths = [file_paths]

        self.playlist = [str(path) for path in file_paths if self.is_audio_file(path)] # Assigning the path of the playlist to the variable
        self.current_track_index = 0 
        if self.playlist: # If playlist exists
            return self.load_track(self.current_track_index) # Appending track by track the path of the track to the playlist if multiple exist or single 
        return False
    
    def load_track(self, index):
        if 0 <= index < len(self.playlist):
            self.current_track_index = index
            track = self.playlist[self.current_track_index]
            try:
                pygame.mixer.music.load(track)
                pygame.mixer.music.set_volume(self.volume)
                self.music_file = track
                return True 
            except pygame.error as e:
                print(f"Error loading track: {e}")
        return False


    def load(self, file_path):
        return self.load_playlist(file_path)
    
    def seek(self, seconds):
        if self.playlist:
            pygame.mixer.music.play(start=seconds)
    
    def play(self):
        if self.playlist:
            if not pygame.mixer.music.get_busy() or self.is_paused:
                track_path = self.playlist[self.current_track_index]
                if self.music_file != track_path:
                    pygame.mixer.music.load(track_path)
                    self.music_file = track_path
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False


    def pause(self):
        # Pause current track
        if self.is_playing: # Check if playlist exists
            pygame.mixer.music.pause() # Pause the track using pygame mixer
            self.is_playing = False
            self.is_paused = True
        
    def resume(self):
        # Resume playback
        if self.is_paused: # Checks if current track is paused
            pygame.mixer.music.unpause() # Resumes the track using pygame mixer
            self.is_playing = True
            self.is_paused = False
        elif not self.is_playing and self.music_file: # Checks if track is loaded and playing
            self.play() 
    
    def stop(self):
        # Stop playback
        pygame.mixer.music.stop() # Stop the track using pygame mixer
        self.is_paused = False
        self.is_playing = False

    def next_track(self):
        # Play the next track in the playlist
        if not self.playlist: # Checks if there is a next song in the playlist
            return False
        self.current_track_index = (self.current_track_index + 1) % len(self.playlist) # Changes the track until no next track exists
        if self.load_track(self.current_track_index): # Checks if next track is loaded 
            self.play()
            return True
        return False

    def previous_track(self):
        # Play the previous track in the playlist
        if not self.playlist: # Checks if there is a previous song in the playlist
            return False
        self.current_track_index = (self.current_track_index - 1 + len(self.playlist)) % len(self.playlist) # Changes the track until no previous track exists
        if self.load_track(self.current_track_index): # Checks if previous track is loaded
            self.play()
            return True
        return False

    def set_volume(self, volume):
        # Set volume to a value
        self.volume = max(0.0, min(volume, 1.0)) # Adjust volume on the 0 to 1 scale
        pygame.mixer.music.set_volume(self.volume) # Set volume using pygame mixer

    def get_volume(self):
        # Get current volume
        return self.volume

    def get_position(self):
        return pygame.mixer.music.get_pos() / 1000.0 # Get position of the track in seconds

    def is_audio_file(self, path):
        # Check if file is an audio file
        return Path(path).suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a'] # Check if the file being loaded in an audio file

    def get_current_track_info(self):
        # Get information about current track
        if not self.playlist:
            return None
        track = self.playlist[self.current_track_index]
        return {
            'name': os.path.basename(track), # Track Name
            'path': track, # Track address
            'index': self.current_track_index, # Track index in playlist
            'total': len(self.playlist) # Playlist length
        }

    def cleanup(self):
        # Cleanup up resources used by the music player
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")