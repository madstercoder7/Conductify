# Import
import pygame
import os
import random
from pathlib import Path

# Music Player class 
class MusicPlayer:
    def __init__(self):
        # Class definition
        pygame.mixer.init() 
        self.playlist = [] 
        self.current_track_index = 0 
        self.volume = 0.5   
        self.is_playing = False
        self.is_paused = False 
        self.music_file = None

    def load_playlist(self, file_paths):
        # Load multiple files as a playlist
        if isinstance(file_paths, (str, Path)): 
            file_paths = [file_paths]

        self.playlist = [str(path) for path in file_paths if self.is_audio_file(path)] 
        self.current_track_index = 0 
        if self.playlist: 
            return self.load_track(self.current_track_index)  
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
        if self.is_playing: 
            pygame.mixer.music.pause() 
            self.is_playing = False
            self.is_paused = True
        
    def resume(self):
        # Resume playback
        if self.is_paused: 
            pygame.mixer.music.unpause() 
            self.is_playing = True
            self.is_paused = False
        elif not self.is_playing and self.music_file: 
            self.play() 
    
    def stop(self):
        # Stop playback
        pygame.mixer.music.stop() 
        self.is_paused = False
        self.is_playing = False

    def next_track(self):
        # Play the next track in the playlist
        if not self.playlist: 
            return False
        self.current_track_index = (self.current_track_index + 1) % len(self.playlist) 
        if self.load_track(self.current_track_index): 
            self.play()
            return True
        return False

    def previous_track(self):
        # Play the previous track in the playlist
        if not self.playlist: 
            return False
        self.current_track_index = (self.current_track_index - 1 + len(self.playlist)) % len(self.playlist) 
        if self.load_track(self.current_track_index): 
            self.play()
            return True
        return False

    def set_volume(self, volume):
        # Set volume to a value
        self.volume = max(0.0, min(volume, 1.0)) 
        pygame.mixer.music.set_volume(self.volume) 

    def get_volume(self):
        # Get current volume
        return self.volume

    def get_position(self):
        return pygame.mixer.music.get_pos() / 1000.0 

    def is_audio_file(self, path):
        # Check if file is an audio file
        return Path(path).suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a'] 

    def get_current_track_info(self):
        # Get information about current track
        if not self.playlist:
            return None
        track = self.playlist[self.current_track_index]
        return {
            'name': os.path.basename(track), 
            'path': track, 
            'index': self.current_track_index, 
            'total': len(self.playlist) 
        }

    def cleanup(self):
        # Cleanup up resources used by the music player
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")