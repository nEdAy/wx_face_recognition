import numpy

from wx_face_recognition.download_file import download_file
from wx_face_recognition.face_recognition_server import get_face_count_and_encodings, download_pic, get_face_encodings, \
    get_is_match_face

if __name__ == '__main__':
    file_path = 'cache/faces'
    prefix_cos_url = 'https://face-recognition-1253284991.cos.ap-beijing.myqcloud.com/'
    file_name = "wxf194e4908c3e16f6.o6zAJszmwzvn7LVJBPsJNhS1Zn5U.a4dTbd3CN6LI7a248bfc668a497b501d92f5444eea36.jpg"
    # unknown_face_encodings, count = get_face_count_and_encodings(prefix_cos_url, file_name)
    #    knownFaceEncoding =
    image = download_pic(prefix_cos_url, file_name)
    unknown_face_encodings = get_face_encodings(image)
    known_face_encodings = numpy.fromstring(knownFaceEncoding, sep="  ")
    is_match_face = get_is_match_face(known_face_encodings, unknown_face_encodings)

    print(is_match_face)

# protoc -I . --python_out=. --grpc_out=. --plugin=protoc-gen-grpc=`which grpc_python_plugin` face_recognition.proto
# python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. face_recognition.proto
