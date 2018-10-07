import os
import csv
from LocalToSpotify import Track
from tinytag import TinyTag

class MixxxExportReader:
    def __init__(self):
        pass

    def get_tracks_to_import(self, path):
        if path.endswith('.csv'):
            return self.get_tracks_from_csv(path)
        else:
            return self.get_tracks_in_folder(path)

    def get_tracks_from_csv(self, file):
        tracks = []
        with open(file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title = self.remove_parens(row['Title'])
                artists = self.remove_parens(row['Artist'])
                tracks.append(Track(-1, title, artists))
        return tracks

    def get_tracks_in_folder(self, path):
        with os.scandir(path) as it:
            tracks = []
            for entry in it:
                if entry.is_file():
                    track = self.read_metadata(entry.path)
                    if track is not None:
                        tracks.append(track)
            return tracks

    def read_metadata(self, file):
        try:
            tag = TinyTag.get(file)
            artists = self.remove_parens(tag.artist)
            track_title = self.remove_parens(tag.title)
            # TODO: If tag not exists
            return Track(-1, track_title, artists)

        except Exception as error:
            print(f'Parsing failed for file: {file}')
            print(error)


    def remove_parens(self, string):
        return string.strip().replace('(', '').replace(')', '').lower()

    def get_path(self, argv):
        if len(argv) < 2:
            return input('Specify path of track files: ')
        else:
            return argv[1]
