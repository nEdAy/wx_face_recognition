import os
import time
from concurrent import futures

import face_recognition_pb2
import face_recognition_pb2_grpc
import grpc

import face_recognition

from download_file import download_file
from face_recognition_knn import train, predict

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class FaceRecognition(face_recognition_pb2_grpc.FaceRecognitionServicer):

    def GetFaceCount(self, request, context):
        count = get_face_count_and_encodings(request.prefixCosUrl, request.fileName, request.faceToken)
        return face_recognition_pb2.GetFaceCountReply(count=count)

    def IsMatchFace(self, request, context):
        file_path = 'cache/temps/' + request.faceToken
        save_path = download_pic(request.prefixCosUrl, request.fileName, file_path=file_path)
        is_match_face = get_is_match_face_by_trained(save_path, request.faceToken)
        return face_recognition_pb2.IsMatchFaceReply(isMatchFace=is_match_face)


def download_pic(prefix_cos_url, file_name, file_path):
    save_path = download_file(prefix_cos_url + file_name, file_name, file_path)
    return save_path


def found_face_count(image):
    # Find all the faces in the image using the default HOG-based model.
    # This method is fairly accurate, but not as accurate as the CNN model and not GPU accelerated.
    # See also: find_faces_in_picture_cnn.py
    face_locations = face_recognition.face_locations(image)
    return len(face_locations)


def get_face_encodings(image):
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(image)
    return unknown_face_encodings


def get_face_count_and_encodings(prefix_cos_url, file_name, face_token):
    file_path = 'cache/faces/' + face_token
    save_path = download_pic(prefix_cos_url, file_name, file_path)
    # Load the uploaded image file
    image = face_recognition.load_image_file(save_path)
    count = found_face_count(image)
    if count == 1:
        # STEP 1: Train the KNN classifier and save it to disk
        # Once the model is trained and saved, you can skip this step next time.
        print("Training KNN classifier...")
        save_path = 'trained'
        if not os.path.exists(save_path):
            print('文件夹', save_path, '不存在，重新建立')
            os.makedirs(save_path)
        model_save_path = 'trained/' + face_token + '.clf'
        train('cache/faces', model_save_path=model_save_path, n_neighbors=2)
        print("Training complete!")
        return count
    else:
        return count


def get_is_match_face_by_trained(save_path, face_token):
    # STEP 2: Using the trained classifier, make predictions for unknown images

    print("Looking for faces in {}".format(save_path))

    # Find all people in the image using a trained classifier model
    # Note: You can pass in either a classifier file name or a classifier model instance

    face_token_path = 'trained/' + face_token + '.clf'
    predictions = predict(save_path, model_path=face_token_path)

    # Print results on the console
    for name, (top, right, bottom, left) in predictions:
        print("- Found {} at ({}, {})".format(name, left, top))
        if face_token == name:
            return True

    return False


def get_is_match_face(known_face_encoding, unknown_face_encodings):
    if len(unknown_face_encodings) > 0:
        # See if the first face in the uploaded image matches the known face
        match_results = face_recognition.compare_faces([known_face_encoding], unknown_face_encodings[0])
        return match_results[0]
    else:
        return False


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    face_recognition_pb2_grpc.add_FaceRecognitionServicer_to_server(FaceRecognition(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
    print("server start at [::]:50052")
