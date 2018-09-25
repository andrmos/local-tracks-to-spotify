import os
from tinytag import TinyTag

class MixxxExportReader:
    def __init__(self):
        pass

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
            return { 'artists': artists, 'track_title': track_title }

        except Exception as error:
            print(f'Parsing failed for file: {file}')
            print(error)


    def remove_parens(self, string):
        return string.strip().replace('(', '').replace(')', '').lower()
