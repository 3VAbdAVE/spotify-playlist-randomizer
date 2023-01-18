# Spotify Playlist Randomizer
Initially based on [another randomizer](https://github.com/grantmcconnaughey/Spotify-Playlist-Randomizer), but now works entirely differently.

Brute-force randomizes the tracks in a spotify playlist, or a list of spotify playlists.
Sort-of-solves Spotify&#39;s stupid pain in the ass shuffle:

1. [Spotify will only shuffle the first 100 songs of a playlist from where you selected.](https://community.spotify.com/t5/Ongoing-Issues/Connect-only-plays-100-song-chunks-of-playlists/idi-p/1284690)
This leads to automation problems with large playlists, since your routine needs to reset the shuffle based on songs further down the playlist.

2. [Alexa does not know how to shuffle songs when played from a routine.](https://community.spotify.com/t5/Live-Ideas/echo-Playlists-Alexa-shuffle-command-for-routines/idi-p/4604442) The HomeAssistant intgration for Spotify has a similar problem. It can&#39;t select a specific song in the playlist to shuffle from.

 3. [Why isn't Shuffle shuffling properly?](https://community.spotify.com/t5/FAQs/Why-isn-t-Shuffle-shuffling-properly/ta-p/4684785)
Spotify&#39;s super-secret shuffle algorithm generally means you get to hear the same 30 or 40 tracks in a non-random order and a large part of the playlist never comes up, and that gets worse over time. The solution from Spotify support is overly complex and extra painful for headless automated playback.

No one knows exactly how it works, but Spotify&#39;s shuffle seems to weight based on things like initial track selection. Clearing Spotify&#39;s local cache seems to help.

Using this tool to randomize the actual playlist order solves issues 1 and 2, and it seems to anedcotally help with issue 3.

 ## Operation:
 For each playlist, this tool performs the following steps:
 - Create a list of tracks in the existing playlist
 - Randomize that list
 - Clear the existing playlist
 - Re-add tracks to the existing playlist

### *This is a desctructive operation.*
It&#39;s been reliable for me, but it&#39;s not a bad idea to make a backup copy of your playlist. (Ctrl-A -> Drag to new list in the desktop.)

## Instructions
This is a Spotify API tool, and so you need to jump through a few hoops to use it.

First, create a [Spotify application](https://developer.spotify.com/dashboard/applications).
- Make a note of the application Client ID and Client Secret.
- Make sure you add a Redirect URI in your application's settings. The default URI included in this tool is http&#58;&#47;&#47;localhost&colon;8080/callback/

Next, edit the included .ini file, and rename it to **spotify-randomizer.ini.**
- You can get the application Client ID and Client Secret from the application you created in the previous step.
- On the desktop or web client, right click your profile name, and copy the link to your profile. The user ID is the string after "/user/" and before the "?".
- - https&#58;&#47;&#47;open&period;spotify.com/user/&lsaquo;YOUR USER PROFILE&rsaquo;?si=YYYYYYYYYYYYYYY
- Create a new "playlistX=<PLAYLIST ID>" for each playlist you want to randomize.
- - On the desktop or web client, right click each playlist you want randomized, click "Share" and then copy the link to the playlist. The playlist ID is the string after "/playlist/" and before the "?".
- - https&#58;&#47;&#47;open&period;spotify.com/playlist/&lsaquo;PLAYLIST ID&rsaquo;?si=YYYYYYYYYYYYYYYYY

This application also requires the spotipy python module:
```pip install spotipy```

Finally, run `python main.py`.

You can override the playlists in the configuration with a single playlist id, and you can specify an alternate config file.
```
$ python ./main.py -h
usage: main.py [-h] [-p PLAYLIST] [-c CONFIG]

Randomize spotify playlists.

optional arguments:
  -h, --help            show this help message and exit
  -p PLAYLIST, --playlist PLAYLIST
                        Override config file with one playlist ID to be randomized
  -c CONFIG, --config CONFIG
                        File containing authorization and an optional list of playlists
```

## TODO
I need to do more testing and make sure it'll refresh the auth token reliably over time, and then I can put this on a headless server.