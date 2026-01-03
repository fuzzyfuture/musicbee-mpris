# MusicBee MPRIS Server

A janky MPRIS server for MusicBee running in Wine on Linux. This script allows you to view metadata and control playback from universal media player controllers like [playerctl](https://github.com/altdesktop/playerctl), or desktop widgets such as [PlasMusic Toolbar](https://github.com/ccatterina/plasmusic-toolbar). It also allows you to pass metadata to applications such as [Music Presence](https://github.com/ungive/discord-music-presence), which otherwise does not support MusicBee on Linux. It mostly works.

This script works by relying on the [Now Playing to External Files](https://www.getmusicbee.com/addons/plugins/47/now-playing-to-external-files/) plugin to write the metadata to text & image files. The files are then monitored for changes, and on change, the new metadata is exposed via the MPRIS D-Bus interface. The playback controls work by sending pre-configured hotkeys to the MusicBee application.

## Requirements

- MusicBee running in Wine (setting this up will not be covered here; see [this](https://getmusicbee.com/forum/index.php?topic=42906.0) or [this](https://getmusicbee.com/forum/index.php?topic=30205.30))
- MusicBee [Now Playing to External Files](https://www.getmusicbee.com/addons/plugins/47/now-playing-to-external-files/) plugin
- [xdotool](https://github.com/jordansissel/xdotool) if you wish to enable play/pause/next/prev controls

## Setup

This guide assumes that you have already gotten MusicBee running in Wine with the Now Playing to External Files plugin installed.

### Configuring plugin

![alt text](/docs/image-1.png)

The tags section of the plugin config should be as shown above. If you would like to see other tags, you will need to edit and run the script on your own.

The tags file and album artwork filenames should be `Tags.txt` and `CoverArtwork.jpg` respectively. Make sure they're in the same linux directory (`Z:/`) as eachother. **This is very important! The script will not work if you use other file names or put the files in separate directories.** You will pass the directory in as a parameter to the script later. 

### Configuring Last.fm API

You can optionally pass a Last.fm API key when starting the script. Doing so will cause cover art to be pulled from the Last.fm API, only using the local image file as a fallback.

This is useful for displaying cover art in applications such as [Music Presence](https://github.com/ungive/discord-music-presence), since the cover art will not be displayed if you're using a local file path. You can obtain a Last.fm API key [here](www.last.fm/api/account/create).

### Configuring hotkeys

Hotkeys are optional - you can skip this part if you just want to view metadata and don't care about controlling playback.

![alt text](/docs/image-2.png)

The supported hotkeys are `Multimedia: Next`, `Multimedia: Play/Pause`, and `Multimedia: Previous`. You can set these to whatever you'd like and it should work fine. They will be passed in as optional parameters to the script.

### Running the script

If you've installed the RPM, you should just be able to run `musicbee-mpris`:

```bash
musicbee-mpris [--lastfm_api_key LASTFM_API_KEY] [--play_pause_key PLAY_PAUSE_KEY] [--next_key NEXT_KEY] [--prev_key PREV_KEY] metadata_dir
```

Example with real inputs:

```bash
musicbee-mpris --lastfm_api_key {key} --play_pause_key ctrl+alt+p --next_key ctrl+alt+n --prev_key ctrl+alt+b /home/nate/Music/MusicBee/metadata/
```

Example bash script that opens the MPRIS server alongside MusicBee and stops the server when MusicBee is closed:

```bash
#!/bin/bash
if ! pgrep -x "musicbee-mpris" > /dev/null; then
	musicbee-mpris --lastfm_api_key {key} --play_pause_key ctrl+alt+p --next_key ctrl+alt+n --prev_key ctrl+alt+b /home/nate/Music/MusicBee/metadata/ &
	MPRIS_PID=$!
fi

trap "pkill -9 musicbee-mpris 2>/dev/null" EXIT

wine "$HOME/.wine/drive_c/Program Files (x86)/MusicBee/MusicBee.exe"
```

## Acknowledgements

- [alexdelorenzo](https://github.com/alexdelorenzo) for the [mpris_server](https://github.com/alexdelorenzo/mpris_server) Python library
- boroda for the [Now Playing to External Files](https://www.getmusicbee.com/addons/plugins/47/now-playing-to-external-files/) MusicBee plugin

Thank you! This project would not be possible without your work :-)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Contributing

Although the script is fairly simple, this is the first time I've ever made anything practical in Python. If you see any areas of potential improvement feel free to leave an issue or PR!