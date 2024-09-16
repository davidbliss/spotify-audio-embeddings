from sklearn.neighbors import NearestNeighbors
import numpy as np
from files import (
	db_path
)
import apsw
import json
from contextlib import closing

conn = apsw.Connection(str(db_path))


# build a list of all embedings and a list of all ids

song_vectors_ids = list(conn.execute("SELECT rowid, song_id, embedding FROM songs_vectors_6;"))
rowids = [row[0] for row in song_vectors_ids]
song_ids = [row[1] for row in song_vectors_ids]
embeddings = np.array([json.loads(row[2]) for row in song_vectors_ids])


# find nerest neighbors for each song's embedings
nbrs = NearestNeighbors(n_neighbors=len(embeddings), algorithm='ball_tree').fit(embeddings)
distances, indices = nbrs.kneighbors(embeddings)

conn.execute("""
  DROP TABLE IF EXISTS song_distances;
  
  CREATE TABLE IF NOT EXISTS song_distances (
	song_id TEXT NOT NULL REFERENCES song(id),
	ids JSON NOT NULL, 
  distances JSON NOT NULL 
);""")


for i, n in enumerate(indices):
  index_song_ids = [song_ids[i] for i in n]
  # some output for spot checking results
  this_id = song_ids[n[0]]
  nearest_id = song_ids[n[1]]
  furthest_id = song_ids[n[-1]]

  nearest_distance = distances[i][1]
  furthest_distance = distances[i][-1]

  print("++++")
  # print(index_song_ids)
  print(this_id)
  print(nearest_id, nearest_distance)
  print(index_song_ids[1])
  print(furthest_id, furthest_distance)
  print(index_song_ids[-1])

  # Save the list if indices and distances under each songs ID
  conn.execute("INSERT INTO song_distances VALUES (?, ?, ?);", (this_id, json.dumps(index_song_ids), json.dumps(distances[i].tolist())))


