import sys
import os
import configparser
import spotipy
import spotipy.util
from spotipy.oauth2 import SpotifyClientCredentials
from tinytag import TinyTag


config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['SPOTIFY']['ClientID']
client_secret = config['SPOTIFY']['ClientSecret']
user_id = config['SPOTIFY']['Username']

class LocalToSpotify:
    def __init__(self, config_file_name):
        self.read_config(config_file_name)

    def read_config(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        try:
            self.client_id = config['SPOTIFY']['ClientID']
            self.client_secret = config['SPOTIFY']['ClientSecret']
            self.user_id = config['SPOTIFY']['Username']

        except KeyError:
            print(f'Error reading {config_file_name}.\nRefer to config.ini.example for correct configuration.')
            sys.exit()

        print(f'Successfully read {config_file_name}.')


    def print_tracks(self, path):
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    tag = TinyTag.get(entry.path)
                    search_spotify(tag.artist, tag.title)

    def search_spotify(self, artist, track):
        search_string = f'artist:{artist} track:{track}'
        print(f'Searching for "{search_string}"')

        results = spotify.search(q=search_string)
        tracks = results['tracks']['items']

        if len(tracks) == 0:
            print('Found none')
        else:
            print(f'Found {len(tracks)} tracks')

        for index, track in enumerate(tracks):
            print(f'{index + 1}:')
            id = track['id']
            name = track['name']
            artists = ', '.join([artist['name'] for artist in track['artists']])
            print(f'Name: {name}\nArtists: {artists}\nID: {id}')

        print('\n')

    def create_playlist(self):
        playlist_name = 'Test playlist'
        is_public = False
        description = 'This is a test playlist'
        spotify.user_playlist_create(user_id, playlist_name, public = is_public)

    def authorize(self, scope):
        redirect_port = 43019
        redirect_uri = f'http://127.0.0.1:{redirect_port}/redirect'
        token = spotipy.util.prompt_for_user_token(user_id, scope, client_id = client_id, client_secret = client_secret, redirect_uri = redirect_uri)

        if token:
            return spotipy.Spotify(auth=token)

        else:
            print(f'Can\'t get token for {user_id}')
            sys.exit()


if __name__ == '__main__':
    path = './tracks'
    scope = 'playlist-modify-public playlist-modify-private'
    localToSpotify = LocalToSpotify('config.ini')
    spotipy = localToSpotify.authorize(scope)
