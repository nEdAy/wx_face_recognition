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
        save_temp_dir_path = 'cache/temps/' + request.faceToken
        save_temp_file_path = download_pic(request.prefixCosUrl, request.fileName, dir_path=save_temp_dir_path)
        is_match_face = get_is_match_face_by_trained(save_temp_file_path, request.faceToken)
        return face_recognition_pb2.IsMatchFaceReply(isMatchFace=is_match_face)


def download_pic(prefix_cos_url, file_name, dir_path):
    file_path = download_file(prefix_cos_url + file_name, file_name, dir_path)
    return file_path


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
    save_face_dir_path = 'cache/faces/' + face_token
    if os.path.exists(save_face_dir_path):
        # error
        return -1
    save_face_file_path = download_pic(prefix_cos_url, file_name, save_face_dir_path)
    # Load the uploaded image file
    face_image = face_recognition.load_image_file(save_face_file_path)
    count = found_face_count(face_image)
    if count == 1:
        # STEP 1: Train the KNN classifier and save it to disk
        # Once the model is trained and saved, you can skip this step next time.
        print("Training KNN classifier...")
        face_token_file_path = 'cache/all_face_token.clf'
        train('cache/faces', model_save_path=face_token_file_path, n_neighbors=2)
        print("Training complete!")
        return count
    else:
        os.removedirs(save_face_dir_path)
        return count


def get_is_match_face_by_trained(save_temp_file_path, face_token):
    # STEP 2: Using the trained classifier, make predictions for unknown images
    print("Looking for faces in {}".format(save_temp_file_path))

    # Find all people in the image using a trained classifier model
    # Note: You can pass in either a classifier file name or a classifier model instance
    face_token_file_path = 'cache/all_face_token.clf'

    if not os.path.exists(save_temp_file_path):
        return False

    if not os.path.exists(face_token_file_path):
        os.remove(save_temp_file_path)
        return False

    predictions = predict(save_temp_file_path, model_path=face_token_file_path)

    # Print results on the console
    for name, (top, right, bottom, left) in predictions:
        print("- Found {} at ({}, {})".format(name, left, top))
        if face_token == name:
            return True

    os.remove(save_temp_file_path)
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
    print("server start at [::]:50052")
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
