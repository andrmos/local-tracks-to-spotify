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

def print_tracks(path):
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                tag = TinyTag.get(entry.path)
                search_spotify(tag.artist, tag.title)

def search_spotify(artist, track):
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

def authorize(user_id, scope):
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
    user_id = 'coshr'
    scope = 'playlist-modify-public playlist-modify-private'
    spotipy = authorize(user_id, scope)
