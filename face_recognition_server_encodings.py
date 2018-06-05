import os
import time
from concurrent import futures

import face_recognition_pb2
import face_recognition_pb2_grpc
import grpc

import face_recognition
import numpy as np

from download_file import download_file

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class FaceRecognition(face_recognition_pb2_grpc.FaceRecognitionServicer):

    def GetFaceCount(self, request, context):
        count = get_face_count_and_encodings(request.prefixCosUrl, request.fileName, request.faceToken)
        return face_recognition_pb2.GetFaceCountReply(count=count)

    def IsMatchFace(self, request, context):
        is_match_face = get_is_match_face(request.prefixCosUrl, request.fileName, request.faceToken)
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
    save_encodings_dir_path = 'cache/encodings/'
    save_encodings_file_path = save_encodings_dir_path + face_token + '.npy'
    # if os.path.exists(save_face_dir_path):
    # error
    # return -1
    # if os.path.exists(save_encodings_file_path):
    # error
    # return -1
    save_face_file_path = download_pic(prefix_cos_url, file_name, save_face_dir_path)
    # Load the uploaded image file
    face_image = face_recognition.load_image_file(save_face_file_path)
    count = found_face_count(face_image)
    if count == 1:
        # STEP 1: Train the KNN classifier and save it to disk
        # Once the model is trained and saved, you can skip this step next time.
        print("Get Encodings...")
        known_face_encodings = get_face_encodings(face_image)
        if not os.path.exists(save_encodings_dir_path):
            print('文件夹', save_encodings_dir_path, '不存在，重新建立')
            os.makedirs(save_encodings_dir_path)
        np.save(save_encodings_file_path, known_face_encodings)
        print("Get Encodings Complete!")
        return count
    else:
        os.removedirs(save_face_dir_path)
        return count


def get_is_match_face(prefix_cos_url, file_name, face_token):
    save_temp_dir_path = 'cache/temps/' + face_token
    save_temp_file_path = download_pic(prefix_cos_url, file_name, dir_path=save_temp_dir_path)
    unknown_face_image = face_recognition.load_image_file(save_temp_file_path)
    unknown_face_encodings = get_face_encodings(unknown_face_image)
    save_encodings_dir_path = 'cache/encodings/'
    save_encodings_file_path = save_encodings_dir_path + face_token + '.npy'
    if not os.path.exists(save_encodings_file_path):
        # error
        os.remove(save_temp_file_path)
        return face_recognition_pb2.IsMatchFaceReply(isMatchFace=False)
    known_face_encodings = np.load(save_encodings_file_path)
    if len(unknown_face_encodings) > 0:
        # See if the first face in the uploaded image matches the known face
        match_results = face_recognition.compare_faces(known_face_encodings, unknown_face_encodings[0])
        if match_results[0]:
            is_match_face = True
        else:
            is_match_face = False
            os.remove(save_temp_file_path)
    else:
        is_match_face = False
        os.remove(save_temp_file_path)
    return is_match_face


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
