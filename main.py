#!/usr/bin/env python3

import subprocess
import time
import argparse
import signal
import requests
import sys
import threading
from mpris_server.adapters import MprisAdapter
from mpris_server.server import Server
from mpris_server import EventAdapter, Metadata, MetadataEntries, Paths, PlayState, Position, Rate, Track
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class MetadataFileHandler(FileSystemEventHandler):
  def __init__(self, adapter):
    self.adapter = adapter
    self.last_tags_update = 0
    self.last_art_update = 0

  def on_modified(self, event):
    if event.is_directory:
      return

    now = time.time()
    filename = Path(event.src_path).name

    if filename == 'Tags.txt' and (now - self.last_tags_update) > 0.5:
      print('tags file modified')
      self.adapter.load_tags()
      self.last_tags_update = now
    elif filename == 'CoverArtwork.jpg' and (now - self.last_art_update) > 0.5:
      print('art file modified')
      self.adapter.load_art()
      self.last_art_update = now

class MusicbeeAdapter(MprisAdapter):
  def __init__(self, metadata_dir, lastfm_api_key, play_pause_key, next_key, prev_key):
    self.metadata_dir = metadata_dir
    self.tags_path = str(Path(metadata_dir) / 'Tags.txt')
    self.art_path = str(Path(metadata_dir) / 'CoverArtwork.jpg')
    self.lastfm_api_key = lastfm_api_key

    self.play_pause_key = play_pause_key
    self.next_key = next_key
    self.prev_key = prev_key

    self.artists = ['Unknown']
    self.album = 'Unknown'
    self.album_artists = ['Unknown']
    self.title = 'Unknown'
    self.art_url = ''
    self.play_state = PlayState.PAUSED
    self.event_handler = None
    self.observer = None

    self.load_tags()
    self.load_art()
    self.start_observer()

  def start_observer(self):
    try:
      if self.observer is not None:
        self.observer.stop()
        self.observer.join(timeout=2)
      
      self.observer = Observer()

      file_handler = MetadataFileHandler(self)
      self.observer.schedule(file_handler, path=self.metadata_dir, recursive=False)

      self.observer.start()

      print('started file observer')
    except Exception as e:
      print(f'error starting file observer: {e}')

  def register_event_handler(self, event_handler):
    self.event_handler = event_handler

  def load_tags(self):
    time.sleep(0.2)

    try:
      with open(self.tags_path, 'rt', encoding='utf-8-sig') as file:
        tags = file.read()
        tags_split = tags.split('\t')

        if len(tags_split) >= 3:
          self.artists, self.album, self.title, self.album_artists = tags_split[:4]
          self.artists = self.artists.split(';')
          self.album_artists = self.album_artists.split(';')
          self.play_state = PlayState.PLAYING
        else:
          self.play_state = PlayState.PAUSED
    except Exception as e:
      print(f'could not load tags: {e}')
    
    if self.event_handler is not None:
      self.event_handler.on_title()
      self.event_handler.on_playpause()

  def load_art(self):
    time.sleep(0.2)

    if (self.lastfm_api_key):
      print('last.fm api key passed; fetching art from last.fm')
      self.fetch_art_lastfm()

    if (not self.lastfm_api_key or not self.art_url):
      if (not self.lastfm_api_key):
        print('no last.fm key; loading local cover art')
      else:
        print('last.fm fetch failed; falling back to local cover art')

      try:
        art_path_obj = Path(self.art_path)

        if art_path_obj.stat().st_size >= 650:
          timestamp = int(time.time() * 1000)
          self.art_url = art_path_obj.as_uri() + f"?t={timestamp}"
        else:
          self.art_url = ''
      except Exception as e:
        print(f'could not load local cover art: {e}')
    
    if self.event_handler is not None:
      self.event_handler.on_title()
      self.event_handler.on_playpause()

  def fetch_art_lastfm(self):
    if not self.lastfm_api_key or self.album == 'Unknown':
      self.art_url = ''
      return
    
    try:
      artist = (self.album_artists[0] if self.album_artists and self.album_artists[0] else
                self.artists[0] if self.artists and self.artists[0] else
                None)
      
      if not artist:
        self.art_url = ''
        return

      params = {
        'method': 'album.getinfo',
        'artist': artist,
        'album': self.album,
        'api_key': self.lastfm_api_key,
        'format': 'json'
      }

      response = requests.get('https://ws.audioscrobbler.com/2.0/', params=params, timeout=5)
      response.raise_for_status()

      data = response.json()

      if 'album' in data and 'image' in data['album']:
        self.art_url = data['album']['image'][-1]['#text']
      else:
        self.art_url = ''
    except Exception as e:
      print(f'error fetching art from last.fm: {e}')
      self.art_url = ''

  def run_musicbee_hotkey(self, hotkey):
    if hotkey is None: return
    search = 'MusicBee' if self.title == 'Unknown' else self.title
    subprocess.run(['xdotool', 'search', '--name', search, 'key', hotkey])

  def play(self):
    self.run_musicbee_hotkey(self.play_pause_key)

  def pause(self):
    self.run_musicbee_hotkey(self.play_pause_key)

  def resume(self):
    self.run_musicbee_hotkey(self.play_pause_key)

  def next(self):
    self.run_musicbee_hotkey(self.next_key)

  def previous(self):
    self.run_musicbee_hotkey(self.prev_key)

  def metadata(self) -> Metadata:
    metadata: Metadata = {
      MetadataEntries.ARTISTS: self.artists,
      MetadataEntries.ALBUM: self.album,
      MetadataEntries.TITLE: self.title,
      MetadataEntries.ALBUM_ARTISTS: self.album_artists,
      MetadataEntries.ART_URL: self.art_url
    }

    return metadata
  
  def get_art_url(self, _) -> str:
    return self.art_url
  
  def get_playstate(self) -> PlayState:
    return self.play_state

  def can_fullscreen(self) -> bool: return False
  def can_quit(self) -> bool: return False
  def can_raise(self) -> bool: return False
  def get_desktop_entry(self) -> Paths: return ''
  def get_fullscreen(self) -> bool: return False
  def get_mime_types(self) -> list[str]: return []
  def get_uri_schemes(self) -> list[str]: return []
  def has_tracklist(self) -> bool: return False
  def quit(self): pass
  def set_fullscreen(self, _): pass
  def set_raise(self, _): pass
  
  def can_control(self) -> bool: return True
  def can_go_next(self) -> bool: return True
  def can_go_previous(self) -> bool: return True
  def can_pause(self) -> bool: return True
  def can_play(self) -> bool: return True
  def can_seek(self) -> bool: return False
  
  def get_current_position(self) -> Position: return 0
  def get_maximum_rate(self) -> Rate: return 1.0
  def get_minimum_rate(self) -> Rate: return 1.0
  def get_next_track(self) -> Track: return ''

class MusicbeeEventHandler(EventAdapter):
  def on_title(self): return super().on_title()
  def on_playpause(self): return super().on_playpause()

def main():
  parser = argparse.ArgumentParser(description='A script that runs an MPRIS server for MusicBee running in Wine.')

  parser.add_argument('metadata_dir', type=str, help='The directory that holds both your tags file (Tags.txt) and cover art file (CoverArtwork.jpg)')
  parser.add_argument('--lastfm_api_key', type=str, help='Your Last.fm API key.')
  parser.add_argument('--play_pause_key', type=str, help='Your MusicBee hotkey for play/pause.')
  parser.add_argument('--next_key', type=str, help='Your MusicBee hotkey for next track.')
  parser.add_argument('--prev_key', type=str, help='Your MusicBee hotkey for previous track.')

  args = parser.parse_args()

  musicbee_adapter = MusicbeeAdapter(args.metadata_dir, args.lastfm_api_key, args.play_pause_key, args.next_key, args.prev_key)

  mpris = Server('MusicBee', adapter=musicbee_adapter)
  event_handler = MusicbeeEventHandler(root=mpris.root, player=mpris.player)

  musicbee_adapter.register_event_handler(event_handler)

  def shutdown_handler(signum, frame):
    print('shutting down... :(')
    musicbee_adapter.observer.stop()
    exit(0)

  signal.signal(signal.SIGTERM, shutdown_handler)
  signal.signal(signal.SIGINT, shutdown_handler)

  try:
      mpris.loop()
  except KeyboardInterrupt:
      shutdown_handler(None, None)

if __name__ == '__main__':
  main()
