
from database.models import EmbeddingModel


class EmbeddingCache:
    def __init__(self):
        self._cache = {}                                                          
        self._is_loaded = False

    def load_from_database(self):
        self._cache = EmbeddingModel.get_all()
        self._is_loaded = True
        return len(self._cache)

    def get_cached_embeddings(self):
        if not self._is_loaded:
            self.load_from_database()
        return self._cache

    def refresh(self):
        return self.load_from_database()

    def invalidate(self):
        self._cache = {}
        self._is_loaded = False

    def count(self):
        return len(self._cache)


                                                                
                                                                           
embedding_cache = EmbeddingCache()
