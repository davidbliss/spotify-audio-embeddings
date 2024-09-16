import json
import numpy as np
# https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html#sklearn.cluster.KMeans
from sklearn.cluster import KMeans
# https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html#sklearn.decomposition.PCA
from sklearn.decomposition import PCA
import skops.io as sio
from files import (
	genres_path,
	kmeans_song_load_order_path,
	kmeans_path,
	reduced_embeddings_path,
  previews_dir,
	db_path
)
import apsw
from contextlib import closing

conn = apsw.Connection(str(db_path))
song_vectors_ids = list(conn.execute("SELECT rowid, song_id FROM songs_vectors;"))
rowids = [row[0] for row in song_vectors_ids]
song_ids = [row[1] for row in  song_vectors_ids]

vectors = np.asarray(
	[
		np.load(conn.blobopen('main', 'songs_vectors', 'vector', rowid, False))
		for rowid
		in rowids
	],
	dtype=np.double
)

## first, reduce to 2 dimensions for original chart and playback (visualize.py)
with genres_path.open() as f:
	genres = json.load(f)

reduced_embeddings = PCA(n_components=2).fit_transform(vectors)
kmeans = KMeans(init="k-means++", n_clusters=len(genres), n_init=4).fit(reduced_embeddings)

with open(kmeans_song_load_order_path, 'w') as f:
	json.dump(song_ids, f)

sio.dump(kmeans, kmeans_path)
np.save(reduced_embeddings_path, reduced_embeddings)


## then, reduce to 6 dimensions for new functionality (tbd)
reduced_embeddings_6 = PCA(n_components=6).fit_transform(vectors)
audio_paths = list(previews_dir.glob("*.mp3"))

conn.execute("""CREATE TABLE IF NOT EXISTS songs_vectors_6 (
	song_id TEXT NOT NULL REFERENCES song(id),
	embedding JSON NOT NULL
);""")

with closing(conn.cursor()) as cursor:
    with conn:
      for (file, embedding) in zip(audio_paths, reduced_embeddings_6):
        cursor.execute("INSERT INTO songs_vectors_6 VALUES (?, ?);", (file.stem, (json.dumps((embedding.tolist())))))
