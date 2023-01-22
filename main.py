#!/usr/bin/env python3

import configparser, argparse, logging, os, random, time
import spotipy
#import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from itertools import islice

logger = logging.getLogger('spotify_playlist_randomizer')
current_directory = os.path.dirname(os.path.abspath(__file__))

def parseArgs():
    parser = argparse.ArgumentParser(
    description='Randomize spotify playlists.')
    parser.add_argument(
        '-p', 
        '--playlist', 
        nargs=1,
        type=str, 
        help="Override config file with one playlist ID to be randomized", 
        required=False
        )
    parser.add_argument(
        '-c', 
        '--config',
        nargs=1, 
        type=str, 
        help="File containing authorization and an optional list of playlists", 
        default='spotify-randomizer.ini'
        )
    return parser.parse_args()

def parseConfig(configfile):
    config = configparser.ConfigParser()
    config.read(configfile)
    return config

def sendmsg(msg, sev='info'):
    # Just some simple debuggery
    print(msg)
    getattr(logger, sev)(msg)
    
class SpotifyPlaylistRandomizer(object):
    def __init__(self, config):
        self.username = config.get('auth', 'user_id')
        self._client_id = config.get('auth', 'client_id')
        self._client_secret = config.get('auth', 'client_secret')
        self._cache_path = config.get('auth', 'tokenpath')
        self.auth_manager, self.client = self._create_client()
        # self.client = spotipy.Spotify(auth=self._get_token(
        #     client_id=self._client_id, 
        #     client_secret=self._client_secret, 
        #     redirect_uri=config.get('auth', 'redirect_uri')))
        self.track_ids = []
        
    def _create_client(self):
        scope = 'user-library-read playlist-modify-private playlist-modify-public'
        auth_manager = SpotifyOAuth(
            scope=scope,
            username=self.username,
            redirect_uri='http://localhost/callback/',
            client_id=self._client_id,
            client_secret=self._client_secret,
            cache_path=self._cache_path
        )
        client = spotipy.Spotify(auth_manager=auth_manager)
        return auth_manager, client
    
    def _refresh_client(self):
        token_info = self.auth_manager.cache_handler.get_cached_token()
        try:
            self.auth_manager.is_token_expired(token_info)
        except:
            self.auth_manager, self.client = self._create_client()
            sendmsg("Token has been refreshed.")
        
    def randomize_playlist(self, playlists):
        for playlist_id in playlists:
            # Check token freshness after any potentially long process
            self._refresh_client()
            pl = self.client.user_playlist(self.username, playlist_id)
            track_ids = self.get_playlist_track_ids(playlist_id)
            msg = f'Randomizing playlist: {pl["name"]}.'
            sendmsg(msg)
            random.shuffle(track_ids)
            
            # This is a little wonky, but instead of deleting all the tracks in iterated chunks,
            # replace them all with a single track, and then delete that. Only two API calls 
            # this way.
            sendmsg(f"Clearing existing tracks from the playlist.")
            self.client.user_playlist_replace_tracks(self.username, playlist_id, [track_ids[-1]])
            self.client.user_playlist_remove_all_occurrences_of_tracks(
                self.username,
                playlist_id,
                tracks=[track_ids[-1]]
            )
            self.add_tracks(playlist_id, track_ids)
     
    def add_tracks(self, playlist_id, track_ids):
        count = 1
        it = iter(track_ids)
        # Check token freshness before any potentially long process
        self._refresh_client()
        
        # Spotify has a limit of 100 items in each API call, so run 100 at a time
        while ( batch := tuple(islice(it, 100))):
            try:
                self.client.user_playlist_add_tracks(
                    self.username,
                    playlist_id,
                    batch
                )
            except spotipy.exceptions.SpotifyException as e:
                sendmsg("At least one non-existent track in this batch, adding them one at a time.", 'error')
                if 'Payload contains a non-existing ID' in e.msg:
                    sendmsg("This is probably due to Spotify invalidating tracks in your region.", 'error')
                    self.add_tracks_individually(playlist_id, batch)
                elif 'Invalid track uri' in e.msg:
                    sendmsg(e.msg,'error')
                    self.add_tracks_individually(playlist_id, batch)
                    
            msg = f"Added tracks {str(count)} to {str(count + (len(batch) - 1))} to the playlist."
            sendmsg(msg)
            count += len(batch)
            time.sleep(2)
    
    def add_tracks_individually(self, playlist_id, batch):
        for track in batch:
            try:
                self.client.user_playlist_add_tracks(
                    self.username,
                    playlist_id,
                    [ track ]
                )
            except spotipy.exceptions.SpotifyException as e:
                sendmsg(f"Found a bad track URI in the batch: spotify:track:{track}. Skipping it.")

    # def _get_token(self, client_id, client_secret, redirect_uri):
    #     scope='user-library-read playlist-modify-private playlist-modify-public'
    #     return util.prompt_for_user_token(
    #         username=self.username,
    #         scope=scope,
    #         client_id=client_id,
    #         client_secret=client_secret,
    #         redirect_uri=redirect_uri
    #     )

    def get_playlist_track_ids(self, playlist_id):
        track_ids = []
        number_of_tracks_in_playlist = self.client.user_playlist_tracks(
            self.username,
            playlist_id=playlist_id,
            fields='total')['total']
        
        msg = f'Found {number_of_tracks_in_playlist} tracks in the source playlist'
        sendmsg(msg)
        
        # Spotify paginates results up to a max of 100 per page, so do this in 
        # get these in chunks of 100.
        offset = 0
        while number_of_tracks_in_playlist > len(track_ids):
            limit = 100
            result = self.client.user_playlist_tracks(
                self.username,
                playlist_id=playlist_id,
                fields='items(track(id))',
                limit=limit,
                offset=offset
            )
            track_ids.extend(t['track']['id'] for t in result['items'])
            offset += limit

        # Sanity check
        assert len(track_ids) == number_of_tracks_in_playlist
        
        # Make sure there are no duplicates
        track_ids = list(set(track_ids))
        
        self.track_ids = track_ids
        return track_ids

def main():
    logging.basicConfig(
        filename='debug.log',
        level=logging.INFO
    )
    args = parseArgs()
    config = parseConfig(args.config)

    def job():
        randomizer = SpotifyPlaylistRandomizer(config)
        if args.playlist:
            playlists = args.playlist
            # playlists.append(args.playlist)
        else:
            playlists = [ x[1] for x in config.items('playlists') ]
            
        randomizer.randomize_playlist(playlists)
            
    job()

if __name__ == '__main__':
    main()

