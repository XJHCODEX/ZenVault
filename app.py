# if running locally
from flask import Flask, request, jsonify, render_template, Response, send_file
from dotenv import load_dotenv
import os
import cx_Oracle
import io

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Database credentials (Use environment variables for security)
DB_USER = os.getenv("username")
DB_PASS = os.getenv("password")

# Using connection string locally instead of wallet file.

DB_DSN = os.getenv("DSN")

def get_db_connection():
    """Establish and return a database connection."""
    try:
        connection = cx_Oracle.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        return connection
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Database connection failed: {error.message}")
        return None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv','mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#<--- HOME --->
@app.route('/')
def home():
    """Serves the main UI"""
    return render_template('index.html')

#<--- UPLOAD_PAGE --->
@app.route('/upload_page')
def upload():
    """Serves the main UI"""
    return render_template('upload.html')

#<-- UPLOAD_FILES -->
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and stores it in the database."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    file_name = file.filename.strip().lower()
    file_type = file.content_type  
    file_content = file.read()  # Read binary data

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()

        # Create a BLOB variable
        blob_var = cursor.var(cx_Oracle.BLOB)

        # Check if file already exists
        cursor.execute("SELECT COUNT(*) FROM files WHERE file_name = :file_name", {"file_name": file_name})
        file_exists = cursor.fetchone()[0] > 0

        if file_exists:
            # Update existing file using BLOB Locator
            cursor.execute("""
                UPDATE files 
                SET file_blob = EMPTY_BLOB(), file_type = :file_type 
                WHERE file_name = :file_name
                RETURNING file_blob INTO :file_blob
            """, {
                "file_type": file_type, 
                "file_name": file_name,
                "file_blob": blob_var
            })
        else:
            # Insert new record with an empty BLOB
            cursor.execute("""
                INSERT INTO files (file_name, file_type, file_blob) 
                VALUES (:file_name, :file_type, EMPTY_BLOB())
                RETURNING file_blob INTO :file_blob
            """, {
                "file_name": file_name,
                "file_type": file_type,
                "file_blob": blob_var
            })

        # Extract BLOB locator from the returned list
        blob_locator = blob_var.getvalue()

        if isinstance(blob_locator, list):  
            blob_locator = blob_locator[0]  # Extract first element if it's a list

        if blob_locator is not None:
            blob_locator.write(file_content)  # Write binary content to BLOB

        connection.commit()
        return jsonify({"message": "File uploaded successfully!"}), 200

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    finally:
        cursor.close()
        connection.close()

# <--- DOWNLOAD FILES --->
@app.route('/download/<file_name>', methods=['GET'])
def download_file(file_name):
    """Retrieves a file from the database and serves it for download."""
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT file_blob, file_type FROM files WHERE file_name = :file_name", 
               {"file_name": file_name})
        row = cursor.fetchone()
        if row:
            file_blob, file_type = row
            return send_file(io.BytesIO(file_blob.read()), mimetype=file_type, as_attachment=True, download_name=file_name)
        else:
            return jsonify({"error": "File not found"}), 404
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    finally:
        cursor.close()
        connection.close()

# <--- DELETE FILE --->
@app.route('/delete/<file_name>', methods=['DELETE'])
def delete_file(file_name):
    """Deletes a file from the database."""
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()

        # Check if file exists
        cursor.execute("SELECT COUNT(*) FROM files WHERE file_name = :file_name", {"file_name": file_name})
        if cursor.fetchone()[0] == 0:
            return jsonify({"error": "File not found"}), 404

        # Delete file
        cursor.execute("DELETE FROM files WHERE file_name = :file_name", {"file_name": file_name})
        connection.commit()

        return jsonify({"message": "File deleted successfully!"}), 200

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    finally:
        cursor.close()
        connection.close()

# <--- MEDIA PREVIEW --->
@app.route('/preview/<file_name>', methods=['GET'])
def preview_file(file_name):
    """Handles video streaming with byte-range support."""
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT file_blob, file_type FROM files WHERE file_name = :file_name", {"file_name": file_name})
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "File not found"}), 404

        file_blob, file_type = row

        # Convert `cx_Oracle.LOB` to BytesIO
        file_bytes = io.BytesIO(file_blob.read())

        # Handle video streaming with byte-range support
        range_header = request.headers.get("Range")
        file_size = len(file_bytes.getvalue())

        if range_header:
            # Parse Range header
            range_values = range_header.replace("bytes=", "").split("-")
            range_start = int(range_values[0]) if range_values[0] else 0
            range_end = int(range_values[1]) if len(range_values) > 1 and range_values[1] else file_size - 1

            length = range_end - range_start + 1
            file_bytes.seek(range_start)
            chunk = file_bytes.read(length)

            headers = {
                "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": file_type
            }
            return Response(chunk, 206, headers)

        # Serve entire file if no byte-range request
        return Response(file_bytes.getvalue(), 200, {"Content-Type": file_type})

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    finally:
        cursor.close()
        connection.close()

#<-- FILE_PAGE -->
@app.route('/file_page')
def files():
    return render_template('files.html')

#<-- LIST_FILES -->
@app.route('/files', methods=['GET'])
def list_files():
    """Returns a list of available files stored in the database."""
    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT file_name, file_type FROM files")
        files = cursor.fetchall()

        if not files:
            return jsonify({"message": "No files available"}), 200

        # Convert result into a list of dictionaries
        file_list = [{"file_name": row[0], "file_type": row[1]} for row in files]

        return jsonify({"files": file_list}), 200

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
