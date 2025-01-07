from flask import Flask, request, session, make_response
from flask_cors import CORS
import os
from sqlalchemy import create_engine
from flask_session import Session
from scanner import scan, transform_perspective
import cv2
import numpy as np
import base64

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = 3306
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = None
if MYSQL_USER == 'root':
    MYSQL_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD', None)
else:
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', None)
if MYSQL_PASSWORD is None:
    raise ValueError('Failed to get MySQL password')

engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/db')

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
Session(app)

SIZE_THRESHOLD = 0.1
CONSISTENT_FRAMES = 10

@app.route('/scan/add', methods=['POST'])
def add_scan():
    image = request.files['image']
    image_data = np.frombuffer(image.read(), np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    finished = False

    corners, transformed_image = scan(image)
    if transformed_image is not None:
        current_size = transformed_image.shape[:2]
        previous_size = session.get('previous_size', None)
        if previous_size is not None:
            size_diff = np.abs(np.array(current_size) - np.array(previous_size)) / np.array(previous_size)
            if np.all(size_diff < SIZE_THRESHOLD):
                session['consistent_count'] = session.get('consistent_count', 0) + 1
                if session.get('consistent_count', 0) >= CONSISTENT_FRAMES:
                    finished = True
                    session['corners'] = corners
            else:
                session['consistent_count'] = 0
        session['previous_size'] = current_size

        print(finished)
    
        return {
            'test': session.get('consistent_count', 0),
            'finished': finished,
            'corners': corners.tolist(),
            'transformed_image': base64.b64encode(cv2.imencode('.jpg', transformed_image)[1].tobytes()).decode('utf-8')
        }
    
    return {
        'finished': finished
    }
     


@app.route('/scan/confirm', methods=['POST'])
def confirm_scan():
    image = request.files['image']
    image_data = np.frombuffer(image.read(), np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    corners = np.array(session['corners'])
    corners = corners * [image.shape[1] / 640, image.shape[0] / 400]
    transformed_image = transform_perspective(image, corners)
    # temporary
    cv2.imwrite('scanned_id.jpg', transformed_image)

    return {
        'transformed_image': base64.b64encode(cv2.imencode('.jpg', transformed_image)[1].tobytes()).decode('utf-8')
    }


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)