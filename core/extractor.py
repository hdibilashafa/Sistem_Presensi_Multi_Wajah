
import numpy as np
import tensorflow as tf
from keras_vggface.vggface import VGGFace
from keras_vggface.utils import preprocess_input
from config import Config


class FeatureExtractor:
    def __init__(self):
                                                                            
                                                                              
        self.model = VGGFace(
            model='resnet50',
            include_top=False,
            input_shape=(224, 224, 3),
            pooling='avg'
        )

                                                                        
                                                                         
                                                                        
                                                        
        dummy_input = np.zeros((1, 224, 224, 3), dtype='float32')
        self.model(dummy_input, training=False)

    def extract(self, face_rgb):
        face_batch = np.expand_dims(face_rgb.astype('float32'), axis=0)
        face_preprocessed = preprocess_input(face_batch, version=2)

                                                                       
                                                                    
        embedding = self.model(face_preprocessed, training=False)
        return embedding.numpy().flatten()

    def extract_batch(self, list_of_face_rgb):
        batch = np.array([f.astype('float32') for f in list_of_face_rgb])
        batch_preprocessed = preprocess_input(batch, version=2)
        embeddings = self.model.predict(batch_preprocessed, verbose=0)
        return embeddings

    @staticmethod
    def average_embedding(embeddings):
        return np.mean(embeddings, axis=0)
