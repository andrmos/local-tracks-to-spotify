import sys
import configparser
import spotipy
import spotipy.util
import time
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from similarity.jarowinkler import JaroWinkler
from MixxxExportReader import *
from Track import *
from Playlist import *
from multiprocessing.dummy import Pool as ThreadPool

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap

class LocalToSpotify:
    def __init__(self, config_file_name):
        self.read_config(config_file_name)
        self.tracks_to_add = []
        self.spotify = self.authorize()
        self.added_tracks = []
        self.tracks_already_in_playlist = []
        self.failed_tracks = []

    def read_config(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        try:
            self.client_id = config['SPOTIFY']['ClientID']
            self.client_secret = config['SPOTIFY']['ClientSecret']
            self.user_id = config['SPOTIFY']['Username']

        except KeyError:
            print(f'Error reading {config_file_name}.')
            print('Refer to config.ini.example for correct configuration.')
            sys.exit()

    def find_track(self, track):
        search_string = f'{track.artists} {track.title}'
        results = self.spotify.search(q=search_string)
        tracks = [self.convert_to_object(track) for track in results['tracks']['items']]
        number_of_tracks = len(tracks)

        if number_of_tracks == 0:
            return None
        elif number_of_tracks == 1:
            return self.select_first_track(tracks)
        elif self.are_identical(tracks):
            return self.select_first_track(tracks)
        else:
            best_match = self.best_match(track, tracks)
            if best_match != None:
                return best_match
            else:
                print(f'Found {number_of_tracks} tracks for "{track}".')
                print('Select correct track:')
                return self.select_correct_track(tracks)

    def best_match(self, search_track, tracks):
        jw = JaroWinkler()
        title_similarities = []
        artists_similarities = []
        totals = []
        for track in tracks:
            title_similarity = jw.similarity(search_track.title.lower(), track.title.lower())
            title_similarities.append(title_similarity)
            artists_similarity = jw.similarity(search_track.artists.lower(), track.artists.lower())
            artists_similarities.append(artists_similarity)
            totals.append(artists_similarity + title_similarity)

        max_index = totals.index(max(totals))
        max_total = totals[max_index]
        if max_total > 1.5:
            return tracks[max_index]
        else:
            return None

    def are_identical(self, tracks):
        isrcs = [track.isrc for track in tracks]
        if '' in isrcs:
            # TODO: Check if same title and artists if no isrc?
            return False
        else:
            return len(set(isrcs)) == 1

    def select_first_track(self, tracks):
        return tracks[0]

    def select_correct_track(self, tracks):
        self.print_possible_tracks(tracks)
        return self.get_track_selection(tracks)

    def print_possible_tracks(self, tracks):
        for index, track in enumerate(tracks):
            print(f'{index + 1}: {track}')

    def get_track_selection(self, tracks):
        input_text = 'Select correct track: '
        valid = False
        selected_track_index = -1
        while not valid:
            try:
                selected_track_index = int(input(input_text)) - 1
                if selected_track_index >= 0 and selected_track_index < len(tracks):
                    valid = True
                else:
                    raise ValueError
            except ValueError:
                print('Invalid number')

        return tracks[selected_track_index]

    def convert_to_object(self, spotify_track):
        id = spotify_track['id']
        track_title = spotify_track['name']
        artists = ', '.join([artist['name'] for artist in spotify_track['artists']])
        isrc = ''
        try:
            isrc = spotify_track['external_ids']['isrc']
        except KeyError:
            pass
        return Track(id, track_title, artists, isrc)

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
        try:
            return self.playlist_tracks
        except AttributeError:
            result = self.spotify.user_playlist_tracks(self.user_id, playlist_id = playlist_id)
            tracks = result['items']
            while result['next']:
                result = self.spotify.next(result)
                tracks.extend(result['items'])
            return [self.convert_to_object(track['track']) for track in tracks]

    def track_in_playlist(self, track, playlist_id):
        try:
            tracks = self.get_playlist_tracks(playlist_id)
            track_ids = [track.id for track in tracks]
            if track.id in track_ids:
                return True
            else:
                return False
        except SpotifyException as e:
            if e.http_status == 404:
                print(f'Playlist with id: {playlist_id} was not found')
            return False

    def add_tracks_to_playlist(self, playlist_id, tracks):
        try:
            while len(tracks) != 0:
                batch = []
                for num in range(0, 100):
                    if len(tracks) == 0:
                        break
                    track_to_add = tracks.pop()
                    if self.track_in_playlist(track_to_add, playlist_id):
                        self.tracks_already_in_playlist.append(track_to_add)
                    else:
                        batch.append(track_to_add.id)
                        self.added_tracks.append(track_to_add)
                        self.playlist_tracks.append(track_to_add)
                if len(batch) > 0:
                    self.spotify.user_playlist_add_tracks(self.user_id, playlist_id, batch)

        except SpotifyException as e:
            print(e)
            # Reason: Couldn't add to playlist
            self.failed_tracks.extend(tracks)

    def get_playlists(self):
        try:
            return self.playlists
        except AttributeError:
            result = self.spotify.user_playlists(self.user_id)
            playlists = result['items']
            while result['next']:
                result = self.spotify.next(result)
                playlists.extend(result['items'])
            # Currently not possible to add to other playlist than your own.
            # TODO: Transform to playlist objects. In create as well.
            self.playlists = self.only_own_playlists(playlists)
            return self.playlists

    def only_own_playlists(self, playlists):
        return [playlist for playlist in playlists if playlist['owner']['id'] == self.user_id]

    def playlist_exist(self, playlist_to_search):
        try:
            spotify_playlists = self.get_playlists()
            playlists = [Playlist(playlist['id'], playlist['name']) for playlist in spotify_playlists]
            playlist_ids = [playlist.id for playlist in playlists]

            if playlist_to_search.id in playlist_ids:
                return True
            else:
                return False

        except SpotifyException as e:
            print(e)
            return False

        except Exception as e:
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

    def create_playlist(self):
        playlist_name = input('Enter playlist name: ')
        is_public = False
        result = self.spotify.user_playlist_create(self.user_id, playlist_name, public = is_public)
        created_playlist = Playlist(result['id'], result['name'])
        # TODO: Store playlist object instead
        # TODO: Does not work when creating new playlist
        self.playlists.append(result)
        return created_playlist

    def select_playlist_or_create_new(self):
        print('1: Select existing playlist')
        print('2: Create new playlist')
        user_reponse = input('Select your option: ')
        should_create_playlist = user_reponse == '2'
        playlist = None
        if should_create_playlist:
            playlist = self.create_playlist()
        else:
            playlist = self.select_playlist()

        if not self.playlist_exist(playlist):
            print(f'Error! Playlist "{playlist}" does not exist.')
            print('Exiting...')
            sys.exit()
        else:
            print(f'Adding to playlist: {playlist}')
            return playlist

    def clean_track_metadata_and_find_again(self, track):
        cleaned_track = track.clean_track()
        return self.find_track(cleaned_track)

    def store_playlist_tracks(self, playlist_tracks):
        tracks = []
        for track in playlist_tracks:
            tracks.append(track)
        self.playlist_tracks = tracks

    def add_tracks_to_spotify(self, tracks_to_add):
        playlist = self.select_playlist_or_create_new()
        playlist_tracks = self.get_playlist_tracks(playlist.id)
        self.store_playlist_tracks(playlist_tracks)

        pool = ThreadPool(4)
        # TODO: self.find_track cannot return None. Will crash.
        test_result = pool.map(self.find_track, tracks_to_add)

        #  for track in tracks_to_add:
            #  spotify_track = self.find_track(track)
            #  not_found = spotify_track is None
            #  if not_found:
                #  spotify_track = self.clean_track_metadata_and_find_again(track)

            #  if spotify_track is not None:
                #  self.tracks_to_add.append(spotify_track)
            #  else:
                #  # Reason: Not found
                #  self.failed_tracks.append(track)

        #  self.add_tracks_to_playlist(playlist.id, self.tracks_to_add)
        #  self.print_summary()

    def print_already_in_playlist(self):
        for track in self.tracks_already_in_playlist:
            print(f'Already in playlist: {track}')

    def print_added(self):
        for track in self.added_tracks:
            print(f'Successfully added: {track}')

    def print_failed(self):
        for track in self.failed_tracks:
            print(f'Did not add: {track}')

    def print_statistics(self):
        successful = len(self.added_tracks)
        total = len(self.added_tracks) + len(self.tracks_already_in_playlist) + len(self.failed_tracks)
        print(f'Added {successful}/{total} tracks.')

    def print_summary(self):
        print()
        print('Summary:')
        self.print_already_in_playlist()
        self.print_added()
        self.print_failed()
        print()
        self.print_statistics()

if __name__ == '__main__':
    mixxxExportReader = MixxxExportReader()
    path = mixxxExportReader.get_path(sys.argv)
    tracks_to_import = mixxxExportReader.get_tracks_in_folder(path)

    localToSpotify = LocalToSpotify('config.ini')
    localToSpotify.add_tracks_to_spotify(tracks_to_import)
