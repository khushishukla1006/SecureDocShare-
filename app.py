from flask import Flask, request, jsonify, send_file
import flask
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import uuid
from cryptography.fernet import Fernet
import firebase_admin
from firebase_admin import credentials, storage
import io
from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image, ImageDraw, ImageFont
import tempfile

import logging

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user_id):
    return str(user_id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=int(identity)).one_or_none()

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///documents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Firebase
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "document-24362",
    "private_key_id": "8510643f0ea6efce7796e4344191bdb076325218",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDdiAL4s0Bi5P2M\nlwbgH1jfPJDqLSzaJacBI6UWaFGQGLzIUMDHFJGXHsHS94CmQ4TegQXTXoogjwkf\nkhl1K+h5Kt1jQrWZmTu1s0HBSMBfuIbZTu40aIk6VqWcR75W3v/ZfXCdgYLLsb2v\ne9EafA7V1PpgdkoWGqDQ1v345Uolmx9L0DqhtUOU10A3ZD6hbR85LIda0+3mCv+h\nkNEFOyc4Y8I8cONYhZ5C7NDysHlLfGpHJnPdzLrJCkNlpqYJX7W0BZXddbrr/F43\n5zpk2PZz4d8gv/V3mLU7DcWPdssH0pbELqcE39LNwPJChAyTnMLstBVjDNKhPT93\nLj2KhfOVAgMBAAECggEAMXvDJihsFmsOE8xcdc2qvVq7CAQFQ8krT77VjnbI2UYd\nTSV0mkOG7dmp8+TjMMBeOpFZashwVCt/HzU0SI8BQ6eGgjiRdfjbdI/Q/Uqx5e/C\n92GBJeW/2W8nWQxRgPgY8EzrzdLzE2rlcwBWSfMyISOMteVWUS+rglqzqlgVQubE\nGY4D1YMV10zrUMlyzVH2OAN0VnO1VLQGXvmp5lj5qcRw7eE/4FifJ0nstFIOkVXA\nmIoeywS33hVYUkPmjjKLsMMJF/FmqtK9A10vR4g23w8+FwtEY3nYZHnAZBZs8Okt\nzY5pM/8+/Pj5O0LYInf0viNRbJqaJZ7pIY9+mF5sAQKBgQD2EC+cq+/CSvydRb+z\nm2R1tL7O0PRO++URWtiupaUtx/nkrpJUDKFZYIGssP5Pk70G+wIq4oVRtHyDQRvu\nAsPKuOXlKSZx0D/IpPIex7HmidzXWrD77vG9UViR4OOMHR5Mcph0AR888FiJ8fVo\nQcX0mYShU6YIu9ou7jqHmhyxAQKBgQDmejaZzmiR8oaHNr14UOJ1wS+d0bqe9bx2\nT8/rZHMWKHxI/fGgG+onVQNReaAQuKJFuI1Kula7RnEiRajM8G7fOVTswcQ2y4Ol\n0XRV/gHk49g1CzuhXbvVVZ7xTVSI9AFqU1TsKl/YOerlWLAExoOqoZkwzfH57i6k\nLIl0J0TulQKBgQDVoo/z8sOjaP+SfLBH/C5ok5jmbzzuJn1nZ/yhBWg4K1unVHnv\nR1f/BW8QxErIRHjlyqDDIxClM5K3UpwxNW1QYOAY6nVac3gteChO2Qp4IlH/F9p5\noad4u1uurBZj3BQmQ4hhj2fTvMjiW5S6BAEesPsaJkoNYyu3e1aNzRwEAQKBgAmB\neuUHFVsHpLLI+DGRLHXs3NjmgIrz2a0Lh6jOwMxmKRIdnyyaWiL7J6LhoE9wPgkg\nHnu5icA5nIrsUpT5SaldRPpq13vnEuvw4pp1WoClQRKW/wOdyRR4bpDHPrhTUAeh\nnjwLV16krOJ+sOvRgDa2aYoQxG0pfLT6vUSUJgytAoGAKvdcdbC59SkT1HO/MInk\nTsGrv4cV1LA5A4aVl+blG5vt+TwJ1KitYoL4iTTvTx8znx5EVnfgqkj+YPBN3gpI\negT6R5/GeQsT1VfpTODb8FUvBNB7YmuK1NcOtCZzVwlDGJgbOlViWiLXtqkNyuGe\n/J6OqJBqEuCZLS1ra4gB7xc=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@document-24362.iam.gserviceaccount.com",
    "client_id": "103980401491737228982",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40document-24362.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
})
firebase_admin.initialize_app(cred, {
    'storageBucket': 'document-24362.appspot.com'
})

# Encryption key
cipher_suite = Fernet(Fernet.generate_key())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='owner')
    documents = db.relationship('Document', backref='owner', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    high_priority_key = db.Column(db.String(32), unique=True, nullable=False)
    low_priority_key = db.Column(db.String(32), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        email=data['email'],
        password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user_id': user.id,
            'role': user.role
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_document():
    try:
        current_user_id = get_jwt_identity()
        app.logger.info(f"User {current_user_id} attempting to upload file")
        
        if 'file' not in request.files:
            app.logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        title = request.form.get('title', file.filename)
        app.logger.info(f"File received: {file.filename}, Title: {title}")
        
        if file.filename == '':
            app.logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            app.logger.error(f"File type not allowed: {file.filename}")
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        app.logger.info(f"Generated unique filename: {unique_filename}")
        
        try:
            # Initialize Firebase storage
            try:
                firebase_admin.initialize_app(
                    credentials.Certificate('document-24362-firebase-adminsdk-fbsvc-8510643f0e.json'),
                    {'storageBucket': 'document-24362.appspot.com'}
                )
                app.logger.info("Firebase initialized successfully")
            except ValueError:
                app.logger.info("Firebase already initialized")
            
            bucket = storage.bucket()
            app.logger.info(f"Created bucket reference: {bucket.name}")
            
            blob = bucket.blob(f'documents/{unique_filename}')
            app.logger.info(f"Created blob reference: {blob.name}")
            
            # Read file content
            file_content = file.read()
            app.logger.info(f"File size: {len(file_content)} bytes")
            
            # Upload to Firebase
            blob.upload_from_string(
                file_content,
                content_type=file.content_type
            )
            app.logger.info(f"File uploaded successfully to {blob.name}")
            
            public_url = blob.public_url
            app.logger.info(f"Generated public URL: {public_url}")
            
            document = Document(
                title=title,
                file_path=public_url,
                owner_id=current_user_id,
                high_priority_key=uuid.uuid4().hex,
                low_priority_key=uuid.uuid4().hex,
                expires_at=datetime.utcnow() + timedelta(days=30)  # Default 30 days
            )
            
            db.session.add(document)
            db.session.commit()
            app.logger.info(f"Document saved to database with ID: {document.id}")
            
            return jsonify({
                'document_id': document.id,
                'title': document.title,
                'file_url': document.file_path,
                'high_priority_key': document.high_priority_key,
                'low_priority_key': document.low_priority_key
            }), 201
            
        except Exception as e:
            app.logger.error(f"Error uploading file to Firebase: {str(e)}")
            return jsonify({'error': 'Error uploading file'}), 500
            
    except Exception as e:
        app.logger.error(f"Error in upload_document: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Test endpoint working'}), 200

@app.route('/api/view/<document_id>/<key>', methods=['GET'])
def view_document(document_id, key):
    document = Document.query.get_or_404(document_id)
    
    if not document.is_active:
        return jsonify({'message': 'Access revoked'}), 403
    
    if key != document.high_priority_key and key != document.low_priority_key:
        return jsonify({'message': 'Invalid key'}), 403
    
    # Get file from Firebase Storage
    bucket = storage.bucket()
    blob = bucket.blob(document.file_path)
    
    # Add watermark if low priority key
    if key == document.low_priority_key:
        file_stream = io.BytesIO()
        blob.download_to_file(file_stream)
        file_stream.seek(0)
        
        # Add watermark (implementation depends on file type)
        if document.file_path.endswith('.pdf'):
            reader = PdfReader(file_stream)
            writer = PdfFileWriter()
            
            for page in reader.pages:
                # Create a new page with watermark
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFont("Helvetica", 12)
                
                # Add watermark text
                text = "VIEW ONLY - No Download Allowed"
                text_width = can.stringWidth(text, "Helvetica", 12)
                x = (letter[0] - text_width) / 2
                y = letter[1] / 2
                
                can.saveState()
                can.translate(x, y)
                can.rotate(-45)
                can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
                can.drawString(0, 0, text)
                can.restoreState()
                can.save()
                
                # Move to the beginning of the StringIO buffer
                packet.seek(0)
                
                # Create a new PDF with Reportlab
                new_pdf = PdfReader(packet)
                
                # Add the "watermark" (which is the new pdf) on the existing page
                page.merge_page(new_pdf.pages[0])
                writer.add_page(page)
            
            # Get file-like object to send
            output_stream = io.BytesIO()
            writer.write(output_stream)
            output_stream.seek(0)
            
            return send_file(
                output_stream,
                mimetype='application/pdf',
                as_attachment=False,
                download_name=f'view_{document.title}.pdf'
            )
    
    return send_file(
        io.BytesIO(blob.download_as_bytes()),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=document.title
    )

@app.route('/api/revoke/<document_id>', methods=['POST'])
@jwt_required()
def revoke_access(document_id):
    current_user_id = get_jwt_identity()
    document = Document.query.get_or_404(document_id)
    
    if document.owner_id != current_user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    document.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Access revoked successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("\nServer starting...")
        print(f"Flask version: {flask.__version__}")
        print(f"Python version: {sys.version}")
        print(f"App running at: http://127.0.0.1:5003")
        print("\nRoutes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule}")
    
    from waitress import serve
    serve(app, host='127.0.0.1', port=5003)
