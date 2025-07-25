# Secure Document Sharing Website

A secure document sharing platform with dual access key system built with Flask and Firebase.

## Features

- User authentication system
- Secure document upload and storage
- Dual key system:
  - High Priority Key: Full control (upload, delete, edit, revoke)
  - Low Priority Key: View-only access with watermarks
- Document access control and revocation
- Secure file viewing with disabled download
- Firebase integration for file storage

## Setup

1. Install Python 3.9 or higher
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up Firebase:
   - Create a Firebase project
   - Download service account key
   - Place it in the project root as `service-account-key.json`
6. Run the application:
   ```bash
   python app.py
   ```

## Usage

1. Register a new account
2. Upload documents
3. Generate access keys
4. Share documents with others using low-priority keys
5. Revoke access when needed

## Security Features

- JWT-based authentication
- AES encryption for sensitive data
- Secure file storage
- Access logging
- Key revocation
- Document expiration
- Watermarking for view-only access

## Project Structure

```
.
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
├── static/            # Static files
└── .env               # Configuration file
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
