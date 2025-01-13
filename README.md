# ID Verification System

This project is an ID verification system that allows users to scan their ID cards using their mobile device. The system processes the scanned images to extract and verify the information on the ID cards and compare them with a picture of the person's face in order to verify their identity.

## Features

- Users can scan the front and back of their ID cards and take a picture of their face.
- The system processes the scanned images to extract and verify the information.
- The verification process can be started, canceled, and checked for status.
- The system uses Flask for the backend and SQLAlchemy for database interactions.

## Requirements

- Docker
- Docker Compose

## Setup

1. Clone the repository:

   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a secrets.env file with the following content:

   ```env
   MYSQL_ROOT_PASSWORD="<your_mysql_root_password>"
   MYSQL_PASSWORD="<your_mysql_password>"
   ```

3. Build and run the Docker containers:

   ```sh
   docker-compose up -d
   ```

4. Check if the containers are running:

   ```sh
   docker ps
   ```
    If the backend container is not running, repeat the previous step.

4. The backend service will be available at `http://localhost:5000`.

## Usage

### Starting the Verification Process

1. Start the testing server:

    ```sh
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python testing/app.py
    ```

2. Navigate to `http://localhost:5001/test_page` to start the verification process.

2. Click the "Start Verification" button to be redirected to the verification start page.

### Scanning the ID

1. If you are on a mobile device, the camera will be activated to scan the front and back of your ID card and take a picture of your face.
2. If you are on a desktop, a QR code will be generated for the current page.

### Checking the Verification Status

1. The status of the verification process can be checked by navigating to `http://localhost:5000/api/verification/check_status/<session_id>`.

### Canceling the Verification Process

1. The verification process can be canceled by sending a DELETE request to `http://localhost:5000/api/verification/cancel/<session_id>`.

## API Endpoints

- `POST /api/verification/start`: Start the verification process.
- `DELETE /api/verification/cancel/<session_id>`: Cancel the verification process.
- `POST /api/scan/add/<session_id>`: Add a scanned image.
- `POST /api/scan/restart/<session_id>`: Restart the scan.
- `POST /api/scan/confirm/<session_id>`: Confirm the scan.
- `GET /api/verification/check_status/<session_id>`: Check the verification status.