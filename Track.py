class Track:
    def __init__(self, id, title, artists, isrc = ''):
        self.id = id
        self.title = title
        self.artists = artists
        self.isrc = isrc

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
        return f'{self.artists} - {self.title}'

