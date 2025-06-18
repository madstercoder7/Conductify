import pygame
import os
import random
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import threading

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.music_file = None
        self.volume = 0.5
        self.is_playing = False
        self.is_paused = False
        self.playlist = []
        self.current_track_index = 0
        self.shuffle_mode = False
        self.repeat_mode = False
        self.tempo_multiplier = 1.0
        self.audio_segment = None
        self.play_thread = None
        pygame.mixer.music.set_volume(self.volume)

    def load(self, file_path):
        '''Load a single music file'''
        self.music_file = file_path
        self.playlist = [file_path]
        self.current_track_index = 0
        try:
            pygame.mixer.music.load(file_path)
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def load_playlist(self, file_paths):
        '''Load multiple files as a playlist'''
        self.playlist = [path for path in file_paths if self.is_audio_file(path)]
        if self.playlist:
            self.current_track_index = 0
            self.music_file = self.playlist[0]
            return self.load(self.music_file) 
        return False
    
    def load_folder(self, folder_path):
        '''Load all audio files from a folder'''
        audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
        folder = Path(folder_path)

        if not folder.exists():
            return False
        
        audio_files = []
        for file_path in folder.rglob('*'):
            if file_path.suffix.lower() in audio_extensions:
                audio_files.append(str(file_path))

        if audio_files:
            return self.load_playlist(sorted(audio_files))
        return False
    
    def is_audio_file(self, file_path):
        '''Check if file is an audio file'''
        audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
        return Path(file_path).suffix.lower() in audio_extensions
    
    def play(self, start=0.0):
        '''Play current track'''
        if self.music_file:
            try:
                if not self.is_paused:
                    if self.play_thread:
                        self.stop()
                    self.play_thread = threading.Thread(target=self._play_audio, daemon=True)
                    self.play_thread.start()
                else:
                    pygame.mixer.music.unpause()
                    self.is_paused = False
                self.is_playing = True
                return True
            except Exception as e:
                print(f"Error playing file: {e}")
                return False
        return False

    def _play_audio(self):
        '''Play audio using pydub'''
        play(self.audio_segment)

    def pause(self):
        '''Pause playback'''
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True

    def resume(self):
        '''Resume playback'''
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.is_paused = False
        elif not self.is_playing and self.music_file:
            self.play()

    def toggle_pause(self):
        '''Toggle between pause and resume'''
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def stop(self):
        '''Stop playback'''
        pygame.mixer.music.stop()
        self.is_paused = False
        self.is_playing = False
        self.play_thread = None

    def next_track(self):
        '''Play next track in playlist'''
        if not self.playlist:
            return False
        
        if self.shuffle_mode:
            self.current_track_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)

        self.music_file = self.playlist[self.current_track_index]
        if self.load(self.music_file):
            if self.is_playing or not self.is_paused:
                self.play()
            return True
        return False
    
    def previous_track(self):
        '''Play previous track in the playlist'''
        if not self.playlist:
            return False
        
        if self.shuffle_mode:
            self.current_track_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_track_index = (self.current_track_index - 1) % len(self.playlist)

        self.music_file = self.playlist[self.current_track_index]
        if self.load(self.music_file):
            if self.is_playing or not self.is_paused:
                self.play()
            return True
        return False

    def set_volume(self, volume):
        '''Set volume'''
        self.volume = max(0.0, min(volume, 1.0))
        pygame.mixer.music.set_volume(self.volume)
        if self.audio_segment:
            self.audio_segment = self.audio_segment - (self.audio_segment.dBFS - (self.volume * 20 - 20))

    def get_volume(self):
        '''Get current volume'''
        return self.volume
    
    def volume_up(self, increment=0.1):
        '''Increase volume'''
        self.set_volume(self.volume + increment)

    def volume_down(self, decrement=0.1):
        '''Decrease volume'''
        self.set_volume(self.volume - decrement)

    def set_tempo(self, multiplier):
        '''Set tempo'''
        self.tempo_multiplier = max(0.5, min(multiplier, 2.0))
        if self.audio_segment:
            self.audio_segment = self.audio_segment._spawn(self.audio_segment.raw_data, overrides={
                "frame_rate": int(self.audio_segment.frame_rate * self.tempo_multiplier)
            })

    def get_tempo(self):
        '''Get current tempo'''
        return self.tempo_multiplier
    
    def toggle_shuffle(self):
        '''Toggle shuffle mode'''
        self.shuffle_mode = not self.shuffle_mode
        return self.shuffle_mode
    
    def toggle_repeat(self):
        '''Toggle repeat mode'''
        if not self.repeat_mode:
            self.repeat_mode = 'one'
        elif self.repeat_mode == 'one':
            self.repeat_mode = 'all'
        else:
            self.repeat_mode = False
        return self.repeat_mode
    
    def get_current_track_info(self):
        '''Get info about current track'''
        if self.music_file:
            filename = os.path.basename(self.music_file)
            return {
                'filename': filename,
                'path': self.music_file,
                'index': self.current_track_index,
                'total': len(self.playlist),
                'is_playing': self.is_playing,
                'is_paused': self.is_paused,
                'volume': self.volume,
                'tempo': self.tempo_multiplier,
                'shuffle': self.shuffle_mode,
                'repeat': self.repeat_mode
            }
        return None
    
    def get_playlist_info(self):
        '''Get playlist info'''
        return {
            'tracks': [os.path.basename(track) for track in self.playlist],
            'current_index': self.current_track_index,
            'total_tracks': len(self.playlist)
        }
    
    def is_music_playing(self):
        '''Check if music is playing'''
        return pygame.mixer.music.get_busy() and self.is_playing
    
    def cleanup(self):
        '''Cleanup the pygame mixer'''
        pygame.mixer.quit()

    def gesture_volume_control(self, gesture_intensity):
        '''Control volume based on gesture intensity'''
        volume_change = gesture_intensity * 0.2
        self.set_volume(self.volume + volume_change)

    def gesture_tempo_change(self, direction, intensity):
        '''Control tempo based on gesture direction and intensity'''
        tempo_change = intensity * 0.2
        if direction > 0:
            self.set_tempo(self.tempo_multiplier + tempo_change)
        else:
            self.set_tempo(self.tempo_multiplier - tempo_change)

    def smart_skip(self, direction):
        '''Smart skip based on current playback position'''
        if direction > 0:
            return self.next_track()
        else:
            return self.previous_track()
        
if __name__ == "__main__":
    player = MusicPlayer()
    print("Enhanced Music Player initialized")
    print("Features: Playlist support, gesture controls, volume/tempo control")