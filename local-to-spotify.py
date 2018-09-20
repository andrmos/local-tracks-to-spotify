import os
import configparser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tinytag import TinyTag


config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['SPOTIFY']['ClientID']
client_secret = config['SPOTIFY']['ClientSecret']

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def print_tracks(path):
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                tag = TinyTag.get(entry.path)
                print(f'{tag.artist}: {tag.title}')


if __name__ == '__main__':
    path = './tracks'
    print_tracks(path)
