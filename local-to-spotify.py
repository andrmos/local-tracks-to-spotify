import configparser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['SPOTIFY']['ClientID']
client_secret = config['SPOTIFY']['ClientSecret']

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

if __name__ == '__main__':
    results = spotify.search(q='artist:dino sabatini track:urania', type='track')
    print(results)
