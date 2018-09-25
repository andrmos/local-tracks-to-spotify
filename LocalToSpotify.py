import sys
import configparser
import spotipy
import spotipy.util
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from MixxxExportReader import *

class Track:
    def __init__(self, id, title, artists):
        self.id = id
        self.title = title
        self.artists = artists

    def clean_track(self):
        self.remove_general_artist_words()
        self.remove_general_title_words()
        return self

    def remove_general_title_words(self):
        words_to_remove = ['original', 'mix', 'feat', 'ft.', 'feat.', 'featuring', '&']
        words = self.title.split(' ')
        self.title = ' '.join([word for word in words if word not in words_to_remove]).strip()
        return self

    def remove_general_artist_words(self):
        words_to_remove = ['original', 'mix', 'feat', 'ft.', 'feat.', 'featuring', '&']
        words = self.artists.split(' ')
        self.artists = ' '.join([word for word in words if word not in words_to_remove]).strip()
        return self

    def __str__(self):
        return f'{self.id}: {self.artists} - {self.title}'

class LocalToSpotify:
    def __init__(self, config_file_name):
        self.read_config(config_file_name)
        self.spotify = self.authorize()
        self.added_tracks = []
        self.failed_tracks = []

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

    def find_track(self, track):
        search_string = f'{track.artists} {track.title}'
        results = self.spotify.search(q=search_string)
        spotify_tracks = results['tracks']['items']
        number_of_tracks = len(spotify_tracks)

        print(f'Searching for "{search_string}"')
        if number_of_tracks == 0:
            print('Not found')
            return None

        elif number_of_tracks == 1:
            return self.select_first_track(spotify_tracks)

        else:
            return self.select_correct_track(spotify_tracks)

    def select_first_track(self, spotify_tracks):
        return self.convert_to_object(spotify_tracks[0])

    def select_correct_track(self, spotify_tracks):
        self.print_possible_tracks(spotify_tracks)
        return self.get_user_selection(spotify_tracks)

    def print_possible_tracks(self, spotify_tracks):
        print(f'Found {len(spotify_tracks)} tracks:')
        for index, spotify_track in enumerate(spotify_tracks):
            track = self.convert_to_object(spotify_track)
            print(f'{index + 1}: {track}')

    def get_user_selection(self, spotify_tracks):
        input_text = 'Select correct track: '
        valid = False
        selected_track_index = -1
        while not valid:
            try:
                selected_track_index = int(input(input_text)) - 1
                if selected_track_index >= 0 and selected_track_index < len(spotify_tracks):
                    valid = True
                else:
                    raise ValueError
            except ValueError:
                print('Invalid number')

        selected_track = self.convert_to_object(spotify_tracks[selected_track_index])
        return selected_track

    def convert_to_object(self, spotify_track):
        id = spotify_track['id']
        track_title = spotify_track['name']
        artists = ', '.join([artist['name'] for artist in spotify_track['artists']])
        return Track(id, track_title, artists)

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
        track_ids = [track.id for track in tracks]
        try:
            if len(track_ids) == 0:
                return False
            self.spotify.user_playlist_add_tracks(self.user_id, playlist_id, track_ids)
            return True

        except SpotifyException as error:
            print(error)
            # TODO: If playlist not found, create it?

    def add_tracks_to_spotify(self, tracks):
        for track in tracks:
            spotify_track = self.find_track(track)

            if spotify_track is None:
                cleaned_track = track.clean_track()
                spotify_track = self.find_track(cleaned_track)

            if spotify_track is not None:
                playlist_id = '6u8zVlsX9YTnaOfmdAaTNR'
                success = self.add_tracks_to_playlist(playlist_id, [spotify_track])
                if success:
                    self.added_tracks.append(spotify_track)
                else:
                    self.failed_tracks.append(spotify_track)
            else:
                self.failed_tracks.append(track)

        self.print_added()
        self.print_failed()
        self.print_summary()

    def print_added(self):
        for track in self.added_tracks:
            print(f'Successfully added {track}')

    def print_failed(self):
        for track in self.failed_tracks:
            print(f'{track} was not found')

    def print_summary(self):
        successful = len(self.added_tracks)
        total = len(self.added_tracks) + len(self.failed_tracks)
        print(f'Added {successful}/{total} tracks')


if __name__ == '__main__':
    path = './tracks'
    mixxxExportReader = MixxxExportReader()
    tracks_to_import = mixxxExportReader.get_tracks_in_folder(path)

    localToSpotify = LocalToSpotify('config.ini')
    localToSpotify.add_tracks_to_spotify(tracks_to_import)
