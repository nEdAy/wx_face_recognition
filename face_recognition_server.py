import face_recognition_server_knn
import face_recognition_server_encodings

USE_KNN = True

if __name__ == '__main__':
    if USE_KNN:
        face_recognition_server_knn.serve()
    else:
        face_recognition_server_encodings.serve()
