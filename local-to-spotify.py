import sys
import os
import configparser
import spotipy
import spotipy.util
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tinytag import TinyTag


class LocalToSpotify:
    def __init__(self, config_file_name):
        self.read_config(config_file_name)
        self.spotify = self.authorize()

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

    def get_tracks_in_folder(self, path):
        with os.scandir(path) as it:
            tracks = []
            for entry in it:
                if entry.is_file():
                    tag = TinyTag.get(entry.path)
                    artist = self.remove_parens(tag.artist)
                    track_title = self.remove_parens(tag.title)
                    track = { 'artist': artist, 'track_title': track_title }
                    tracks.append(track)
            return tracks

    def remove_parens(self, string):
        return string.strip().replace('(', '').replace(')', '').lower()


    def find_track(self, artist, track):
        search_string = f'artist:{artist} track:{track}'
        results = self.spotify.search(q=search_string)
        tracks = results['tracks']['items']

        if len(tracks) == 0:
            return None

        # TODO: Fix, currently we just add first one.
        #       Figure out which one to add.
        id = tracks[0]['id']
        track_title = tracks[0]['name']
        artists = ', '.join([artist['name'] for artist in tracks[0]['artists']])
        track = { 'id': id, 'track_title': track_title, 'artists': artists }
        return track


    def create_playlist(self):
        playlist_name = 'Test playlist'
        is_public = False
        description = 'This is a test playlist'
        self.spotify.user_playlist_create(self.user_id, playlist_name, public = is_public)

    def authorize(self):
        scope = 'playlist-modify-public playlist-modify-private playlist-read-private'
        redirect_port = 43019
        redirect_uri = f'http://127.0.0.1:{redirect_port}/redirect'
        token = spotipy.util.prompt_for_user_token(self.user_id, scope, client_id = self.client_id, client_secret = self.client_secret, redirect_uri = redirect_uri)

        if token:
            return spotipy.Spotify(auth=token)

        else:
            print(f'Can\'t get token for {self.user_id}')
            sys.exit()

    # TODO: Playlist id in config or create new playlist.
    def add_tracks_to_playlist(self, playlist_id, tracks):
        '''
        tracks: dict with fields: id, track_title, artists
        '''
        # TODO: If not exists in playlist already
        track_ids = [track['id'] for track in tracks]
        try:
            if len(track_ids) == 0:
                return
            self.spotify.user_playlist_add_tracks(self.user_id, playlist_id, track_ids)

            track_title = track['track_title']
            artist = track['artist']
            print(f'Successfully added {track_title}')

        except SpotifyException as error:
            print(error)
            # TODO: If playlist not found, create it?

    def remove_general_words(self, track_title):
        words_to_remove = ['original', 'mix', 'feat', 'ft.', 'feat.', 'featuring', '&']
        words = track_title.split(' ')
        cleaned = [word for word in words if word not in words_to_remove]
        return ' '.join(cleaned).strip()


if __name__ == '__main__':
    path = './tracks'
    localToSpotify = LocalToSpotify('config.ini')
    local_tracks = localToSpotify.get_tracks_in_folder(path)

    for track in local_tracks:
        spotify_track = localToSpotify.find_track(track['artist'], track['track_title'])

        if spotify_track is None:
            cleaned_track_title = localToSpotify.remove_general_words(track['track_title'])
            # TODO Clean artists as well?
            spotify_track = localToSpotify.find_track(track['artist'], cleaned_track_title)

        if spotify_track is not None:
            playlist_id = '6u8zVlsX9YTnaOfmdAaTNR'
            localToSpotify.add_tracks_to_playlist(playlist_id, [spotify_track])
        else:
            track_artist = track['artist']
            track_title = track['track_title']
            print(f'{track_artist} - {track_title} was not found')
