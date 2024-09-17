from files import (
	db_path,
  previews_dir
)
import numpy as np
import apsw
import json
import pygame
from pygame.locals import *

# works in Visual Studio Code's terminal
def link(uri, label=None):
    if label is None: 
        label = uri
    parameters = ''

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'

    return escape_mask.format(parameters, uri, label)

def build_text(t_string, x, y):
  text = font.render(t_string, True, white, black)
  textRect = text.get_rect()
  textRect.topleft = (x, y)  
  DISPLAYSURF.blit(text, textRect)  

def get_songs():
  global line1, track1, line2, track2, line3, track3
  #check a random song
  song_distances = list(conn.execute("SELECT song_id, ids, distances FROM song_distances ORDER by RANDOM()"))

  # check a specific song
  # song_distances = list(conn.execute("SELECT song_id, ids, distances FROM song_distances WHERE song_id = 'spotify:track:7zuuWZo0MyOdG3VHg1Mgml'"))

  this_id = song_distances[0][0]
  sorted_ids = np.array(json.loads(song_distances[0][1]))
  sorted_distances = np.array(json.loads(song_distances[0][2]))

  nearest_id = sorted_ids[1]
  furthest_id = sorted_ids[-1]
  nearest_distance = sorted_distances[1]
  furthest_distance = sorted_distances[-1]

  print(this_id, link('https://open.spotify.com/track/' + this_id.split(":")[2]))
  print(nearest_id, nearest_distance, link('https://open.spotify.com/track/' + nearest_id.split(":")[2]))
  print(furthest_id, furthest_distance, link('https://open.spotify.com/track/' + furthest_id.split(":")[2]))

  track1 = this_id
  track2 = nearest_id
  track3 = furthest_id

  songs = [
            conn.execute(
              """
                WITH
                  artists as (
                    SELECT
                      group_concat(artists.value ->> '$.name', ' | ') as artist
                    FROM
                      songs,
                      json_each(songs.info, '$.artists') as artists
                    WHERE
                      songs.id = ?
                  )
                SELECT
                  songs.id,
                  songs.info ->> '$.name' as title,
                  artists.artist,
                  group_concat(songs_genres.genre, ', ') as genres
                FROM
                  songs,
                  artists
                LEFT JOIN
                  songs_genres ON songs.id = songs_genres.song_id
                WHERE
                  songs.id = ?;
              """,
              (song_id, song_id)
            ).fetchone()
            for song_id
            in [track1, track2, track3]
          ]
  print(songs)

  line1 = f'1.  {songs[0][1]} by {songs[0][2]}, {songs[0][3]}' 
  line2 = f'2.  {songs[1][1]} by {songs[1][2]}, {songs[1][3]} distance: {str(nearest_distance)}'
  line3 = f'3.  {songs[2][1]} by {songs[2][2]}, {songs[2][3]} distance: {str(furthest_distance)}'

conn = apsw.Connection(str(db_path))


get_songs()

pygame.init()
size = (700, 500)
screen = pygame.display.set_mode(size)
DISPLAYSURF = pygame.display.set_mode((800, 300))

font = pygame.font.Font('freesansbold.ttf', 18)

black = (0, 0, 0)
white = (255, 255, 255)


#Game loop begins
while True:
  for event in pygame.event.get():
    if event.type == QUIT:
        pygame.quit()
        sys.exit()
    if event.type == pygame.KEYDOWN:
      if event.key == K_SPACE:
        pygame.mixer.music.pause()
        get_songs()
      if event.key == K_1:
        pygame.mixer.music.load(previews_dir / f"{track1}.mp3")
        pygame.mixer.music.play(-1)
      if event.key == K_2:
        pygame.mixer.music.load(previews_dir / f"{track2}.mp3")
        pygame.mixer.music.play(-1)
      if event.key == K_3:
        pygame.mixer.music.load(previews_dir / f"{track3}.mp3")
        pygame.mixer.music.play(-1)
      if event.key == K_p:
        if pygame.mixer.music.get_busy():
          pygame.mixer.music.pause()
        else:
          pygame.mixer.music.unpause()
      elif event.key == K_m:
        if pygame.mixer.music.get_volume() != 0:
          pygame.mixer.music.set_volume(0)
        else:
          pygame.mixer.music.set_volume(1)

  screen.fill((0,0,0))
  build_text(line1, 10, 25)
  build_text(line2, 10, 125)
  build_text(line3, 10, 225)
  pygame.display.update()
