from flask import Flask, request
import os
from scanner import scan, transform_perspective
import cv2
import numpy as np
import base64
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger
import random

# MySQL configuration
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

# Flask app configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# Flask SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Corners(db.Model):
    __tablename__ = 'corners'

    id = db.Column(db.Integer, primary_key=True)
    x1 = db.Column(db.Float, nullable=False)
    y1 = db.Column(db.Float, nullable=False)
    x2 = db.Column(db.Float, nullable=False)
    y2 = db.Column(db.Float, nullable=False)
    x3 = db.Column(db.Float, nullable=False)
    y3 = db.Column(db.Float, nullable=False)
    x4 = db.Column(db.Float, nullable=False)
    y4 = db.Column(db.Float, nullable=False)

class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(BigInteger, primary_key=True, autoincrement=False)
    front_corners_id = db.Column(db.Integer, db.ForeignKey('corners.id'), nullable=False)
    back_corners_id = db.Column(db.Integer, db.ForeignKey('corners.id'), nullable=True)
    consistent_count = db.Column(db.Integer, nullable=False)
    previous_size = db.Column(db.PickleType, nullable=False)
    status = db.Column(db.Enum('IN_PROGRESS', 'WAITING', 'DENIED', 'ACCEPTED', name='status_enum'), nullable=False)
    callback_url = db.Column(db.String(255), nullable=False)

    front_corners = db.relationship('Corners', backref=db.backref('session', uselist=False), cascade='all, delete-orphan')
    back_corners = db.relationship('Corners', backref=db.backref('session', uselist=False), cascade='all, delete-orphan')

with app.app_context():
    db.create_all()

# Constants for the scanning process
SIZE_THRESHOLD = 0.1
CONSISTENT_FRAMES = 10

@app.route('/verification/start', methods=['POST'])
def verification_start():
    # The callback URL is used to send the result of the verification process
    callback_url = request.json.get('callback_url')
    if not callback_url:
        return "Callback URL is required", 400

    session_id = None
    while True:
        session_id = random.randint(1, 9_223_372_036_854_775_807) # the ids are random to prevent people from guessing someone else's session id
        if  db.session.query(Session).filter_by(id=session_id).first() is None:
            break
    new_session = Session(id=session_id, callback_url=callback_url, consistent_count=0, previous_size=None, status='IN_PROGRESS')
    db.session.add(new_session)
    db.session.commit()

    return {"session_id": session_id}, 201

@app.route('/scan/add/<session_id>', methods=['POST'])
def add_scan(session_id):
    session = db.session.query(Session).filter_by(id=session_id).first()
    if session is None:
        return "Session not found", 404
    if session.consistent_count >= CONSISTENT_FRAMES:
        return "Scan already finished", 400
    image = request.files['image']
    image_data = np.frombuffer(image.read(), np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    finished = False

    corners, transformed_image = scan(image)
    # bellow is the logic that checks for a number of consistent frames. When the required number is reached the scan is successful
    if transformed_image is not None:
        current_size = transformed_image.shape[:2]
        previous_size = session.previous_size
        if previous_size is not None:
            size_diff = np.abs(np.array(current_size) - np.array(previous_size)) / np.array(previous_size)
            if np.all(size_diff < SIZE_THRESHOLD):
                session.consistent_count += 1
                if session.consistent_count >= CONSISTENT_FRAMES:
                    finished = True
                    corners_obj = Corners(x1=corners[0, 0], y1=corners[0, 1], x2=corners[1, 0], y2=corners[1, 1], x3=corners[2, 0], y3=corners[2, 1], x4=corners[3, 0], y4=corners[3, 1]) # I hate this line
                    db.session.add(corners_obj)
                    if session.front_corners is None:
                        session.front_corners = corners_obj
                        session.consistent_count = 0
                    else:
                        session.back_corners = corners_obj
            else:
                session.consistent_count = 0
        session.previous_size = current_size

        db.session.commit()
    
        return {
            'test': session.consistent_count,
            'finished': finished,
            'corners': corners.tolist(),
            'transformed_image': base64.b64encode(cv2.imencode('.jpg', transformed_image)[1].tobytes()).decode('utf-8') # I have to check if anything here is unnecessary
        }
    
    return {
        'finished': finished
    }
     


# Needs to be rewritten to receive 3 images!
@app.route('/scan/confirm/<session_id>', methods=['POST'])
def confirm_scan(session_id):
    session = db.session.query(Session).filter_by(id=session_id).first()
    if session is None:
        return "Session not found", 404
    if session.consistent_count < CONSISTENT_FRAMES:
        return "Scan not finished", 400
    
    front_image = request.files['front_image']
    back_image = request.files['back_image']
    face_image = request.files['face_image']

    front_image_data = np.frombuffer(front_image.read(), np.uint8)
    back_image_data = np.frombuffer(back_image.read(), np.uint8)
    face_image_data = np.frombuffer(face_image.read(), np.uint8)

    front_image = cv2.imdecode(front_image_data, cv2.IMREAD_COLOR)
    back_image = cv2.imdecode(back_image_data, cv2.IMREAD_COLOR)
    face_image = cv2.imdecode(face_image_data, cv2.IMREAD_COLOR)

    c = session.front_corners
    corners = np.array([[c.x1, c.y1], [c.x2, c.y2], [c.x3, c.y3], [c.x4, c.y4]]) # this one too
    corners = corners * [front_image.shape[1] / 640, front_image.shape[0] / 400]
    front_transformed_image = transform_perspective(front_image, corners)

    c = session.back_corners
    corners = np.array([[c.x1, c.y1], [c.x2, c.y2], [c.x3, c.y3], [c.x4, c.y4]])
    corners = corners * [back_image.shape[1] / 640, back_image.shape[0] / 400]
    back_transformed_image = transform_perspective(back_image, corners)

    # temporary
    cv2.imwrite('front_scanned_id.jpg', front_transformed_image)
    cv2.imwrite('back_scanned_id.jpg', back_transformed_image)
    # Has to process the image.

    return {
        'front_transformed_image': base64.b64encode(cv2.imencode('.jpg', front_transformed_image)[1].tobytes()).decode('utf-8'),
        'back_transformed_image': base64.b64encode(cv2.imencode('.jpg', back_transformed_image)[1].tobytes()).decode('utf-8')
    }

@app.route('/verification/check_status/<session_id>', methods=['GET'])
def check_status(session_id):
    session = db.session.query(Session).filter_by(id=session_id).first()
    if session is None:
        return "Session not found", 404

    return {
        'status': session.status
    }

@app.route('/admin/review', methods=['GET'])
def review_list():
    pass

@app.route('/admin/review/<session_id>', methods=['GET', 'POST'])
def review(session_id):
    pass

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)