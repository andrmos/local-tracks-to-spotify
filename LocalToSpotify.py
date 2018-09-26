import sys
import configparser
import spotipy
import spotipy.util
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from MixxxExportReader import *
from Track import *
from Playlist import *

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
        return self.get_track_selection(spotify_tracks)

    def print_possible_tracks(self, spotify_tracks):
        print(f'Found {len(spotify_tracks)} tracks:')
        for index, spotify_track in enumerate(spotify_tracks):
            track = self.convert_to_object(spotify_track)
            print(f'{index + 1}: {track}')

    def get_track_selection(self, spotify_tracks):
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

    def get_playlist_tracks(self, playlist_id):
        result = self.spotify.user_playlist_tracks(self.user_id, playlist_id = playlist_id)
        tracks = result['items']
        while result['next']:
            result = self.spotify.next(result)
            tracks.extend(result['items'])
        return tracks

    def track_in_playlist(self, track, playlist_id):
        try:
            tracks = self.get_playlist_tracks(playlist_id)
            track_ids = [track['track']['id'] for track in tracks]
            if track.id in track_ids:
                return True
            else:
                return False
        except SpotifyException as e:
            if e.http_status == 404:
                print(f'Playlist with id: {playlist_id} was not found')
            return False

    def add_tracks_to_playlist(self, playlist_id, track):
        if self.track_in_playlist(track, playlist_id):
            print(f'{track} already in playlist')
            return False
        try:
            self.spotify.user_playlist_add_tracks(self.user_id, playlist_id, [track.id])
            return True

        except SpotifyException as e:
            print(e)
            return False

    def get_playlists(self):
        result = self.spotify.user_playlists(self.user_id)
        playlists = result['items']
        while result['next']:
            result = self.spotify.next(result)
            playlists.extend(result['items'])
        # Currently not possible to add to other playlist than your own.
        return self.only_own_playlists(playlists)

    def only_own_playlists(self, playlists):
        return [playlist for playlist in playlists if playlist['owner']['id'] == self.user_id]

    def playlist_exist(self, playlist_to_search):
        try:
            spotify_playlists = self.get_playlists()
            playlists = [Playlist(playlist['id'], playlist['name']) for playlist in spotify_playlists]
            playlist_ids = [playlist.id for playlist in playlists]

            if playlist_to_search.id in playlist_ids:
                print(f'Playlist "{playlist_to_search}" found')
                return True
            else:
                print(f'Playlist "{playlist_to_search}" not found')
                return False

        except SpotifyException as e:
            print(e)
            return False

    def search_for_playlists(self):
        search_query = input('Search for playlist: ')
        all_playlists = self.get_playlists()
        return [playlist for playlist in all_playlists if search_query.lower() in playlist['name'].lower()]

    def print_playlist_options(self, playlists):
        for index, playlist in enumerate(playlists):
            name = playlist['name']
            print(f'{index + 1}: {name}')
        print('s: search again')

    def get_playlist_selection(self, playlists):
        selected_index = -1
        valid = False
        while not valid:
            user_input = input('Select playlist: ')
            if user_input == 's':
                playlists = self.search_for_playlists()
                self.print_playlist_options(playlists)
            else:
                selected_index = self.parse_input(user_input) - 1
                min = 0
                max = len(playlists)
                valid = self.validate_playlist_selection(selected_index, min, max)
        return selected_index

    def select_playlist(self):
        playlists = self.search_for_playlists()
        self.print_playlist_options(playlists)
        selected_index = self.get_playlist_selection(playlists)
        id = playlists[selected_index]['id']
        name = playlists[selected_index]['name']
        return Playlist(id, name)

    def parse_input(self, selection):
        try:
            return int(selection)
        except ValueError:
            return -1

    def validate_playlist_selection(self, selection, min, max):
        return selection >= min and selection < max

    def add_tracks_to_spotify(self, tracks):
        playlist = self.select_playlist()
        if not self.playlist_exist(playlist):
            # TODO: Create playlist.
            print('Exiting...')
            sys.exit()

        for track in tracks:
            spotify_track = self.find_track(track)

            if spotify_track is None:
                cleaned_track = track.clean_track()
                spotify_track = self.find_track(cleaned_track)

            if spotify_track is not None:
                success = self.add_tracks_to_playlist(playlist.id, spotify_track)
                if success:
                    self.added_tracks.append(spotify_track)
                else:
                    self.failed_tracks.append(spotify_track)

            else:
                self.failed_tracks.append(track)

        # TODO: Clean up printing
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
