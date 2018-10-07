import os
import csv
from LocalToSpotify import Track
from tinytag import TinyTag

class MixxxExportReader:
    def __init__(self, path):
        self.path = path

    def get_tracks_to_import(self):
        if self.path.endswith('.csv'):
            return self.get_tracks_from_csv()
        else:
            return self.get_tracks_in_folder()

    def get_tracks_from_csv(self):
        tracks = []
        with open(self.path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title = self.remove_parens(row['Title'])
                artists = self.remove_parens(row['Artist'])
                tracks.append(Track(-1, title, artists))
        return tracks

    def get_tracks_in_folder(self):
        with os.scandir(self.path) as it:
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
