
import numpy as np


class FaceMatcher:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def set_threshold(self, threshold):
        self.threshold = threshold

    @staticmethod
    def cosine_similarity(embedding_a, embedding_b):
        dot_product = np.dot(embedding_a, embedding_b)
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def match(self, query_embedding, reference_embeddings):
        if not reference_embeddings:
            return {
                'recognized': False,
                'user_id': None,
                'nama': 'Unknown',
                'similarity': 0.0
            }

        best_score = -1.0
        best_user_id = None
        best_nama = 'Unknown'

        for user_id, data in reference_embeddings.items():
            score = self.cosine_similarity(query_embedding, data['embedding'])
            if score > best_score:
                best_score = score
                best_user_id = user_id
                best_nama = data['nama']

        if best_score >= self.threshold:
            return {
                'recognized': True,
                'user_id': best_user_id,
                'nama': best_nama,
                'similarity': best_score
            }
        else:
            return {
                'recognized': False,
                'user_id': None,
                'nama': 'Unknown',
                'similarity': best_score
            }

    def match_batch(self, query_embeddings, reference_embeddings):
        return [self.match(emb, reference_embeddings) for emb in query_embeddings]
