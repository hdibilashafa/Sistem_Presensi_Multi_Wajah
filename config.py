import os

class Config:
                         
    SECRET_KEY = 'face_recognition_secret_key_2024'
                                                                     
                                                                     
                                                                  
                                                                        
    DEBUG = False

                         
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''                                    
    MYSQL_DB = 'presensi_multiwajah_jarakjauh'
    MYSQL_CURSORCLASS = 'DictCursor'

                                
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATASET_FOLDER = os.path.join(BASE_DIR, 'dataset')

                          
    CAMERA_INDEX = 0
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

                                         
    MIN_FACE_SIZE = 20
    MTCNN_THRESHOLDS = [0.6, 0.7, 0.7]
    MTCNN_SCALE_FACTOR = 0.709

                                               
    INPUT_SIZE = (224, 224)                                                 
    IMAGE_FORMAT = 'RGB'

                                     
                                                                     
    ENHANCEMENT_THRESHOLD = 224
    CLAHE_CLIP_LIMIT = 2.0
    CLAHE_TILE_GRID_SIZE = (8, 8)
    UNSHARP_SIGMA = 1.0
    UNSHARP_STRENGTH = 1.5

                                     
    DEFAULT_THRESHOLD = 0.5                                                              

                                                     
    REGISTRATION_DISTANCES = [1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00]
    REGISTRATION_EXPRESSIONS = [
        'netral', 'bahagia', 'sedih', 'marah', 'terkejut', 'jijik', 'takut'
    ]
    PHOTOS_PER_USER = len(REGISTRATION_DISTANCES) * len(REGISTRATION_EXPRESSIONS)           

                                          
    BBOX_COLOR_RECOGNIZED = (0, 255, 0)                       
    BBOX_COLOR_UNKNOWN = (0, 0, 255)                                
    BBOX_THICKNESS = 2
