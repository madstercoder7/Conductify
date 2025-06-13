import pygame

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.music_file = None
        self.volume = 0.5
        pygame.mixer.music.set_volume(self.volume)

    def load(self, file_path):
        self.music_file = file_path
        pygame.mixer.music.load(file_path)

    def play(self):
        if self.music_file:
            pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def set_volume(self, volume):
        self.volume = max(0.0, min(volume, 1.0))
        pygame.mixer.music.set_volume(self.volume)

    def get_volume(self):
        return pygame.mixer.music.get_volume()