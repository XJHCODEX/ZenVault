from flask import Flask, g, request, jsonify, render_template, Response, send_file, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import cx_Oracle
import io
from flask_wtf.csrf import CSRFProtect
from forms import LoginForm, RegisterForm

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "a-secure-random-string")

load_dotenv()

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database credentials
DB_USER = os.getenv("username")
DB_PASS = os.getenv("password")
DB_DSN = os.getenv("DSN")

# Initialize connection pool
def init_pool():
    """Create and return a cx_Oracle connection pool."""
    try:
        pool = cx_Oracle.SessionPool(
            user=DB_USER,
            password=DB_PASS,
            dsn=DB_DSN,
            min=2,          # Minimum number of connections
            max=10,         # Maximum number of connections
            increment=1,     # Connections to add when needed
            encoding="UTF-8"
        )
        print("Connection pool created successfully")
        return pool
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Failed to create connection pool: {error.message}")
        return None

# Store pool in app config
app.config['DB_POOL'] = init_pool()

# Manage connections per request
@app.before_request
def before_request():
    """Acquire a connection from the pool for the request."""
    if app.config['DB_POOL']:
        g.db_conn = app.config['DB_POOL'].acquire()
    else:
        g.db_conn = None

@app.teardown_request
def teardown_request(exception):
    """Release the connection back to the pool."""
    if hasattr(g, 'db_conn') and g.db_conn is not None:
        app.config['DB_POOL'].release(g.db_conn)

def get_db_connection():
    """Return the connection from the current request context."""
    if not hasattr(g, 'db_conn') or g.db_conn is None:
        raise Exception("No database connection available")
    return g.db_conn

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# <-- REGISTER -->
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        username = register_form.username.data.lower()
        password = register_form.password.data
        password_hash = generate_password_hash(password)
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Check for existing user
                cursor.execute(
                    "SELECT id FROM users WHERE LOWER(username) = :username",
                    {'username': username}
                )
                if cursor.fetchone():
                    return render_template('register.html', register_form=register_form, error='Username already exists')
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (:username, :password)",
                    {'username': username, 'password': password_hash}
                )
                conn.commit()
                print(f"User {username} registered successfully")
                return redirect(url_for('login'))
        except cx_Oracle.IntegrityError:
            return render_template('register.html', register_form=register_form, error="Username already exists")
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            return render_template('register.html', register_form=register_form, error=f"Database error: {error.message}")
        except Exception as e:
            return render_template('register.html', register_form=register_form, error=str(e))
    return render_template('register.html', register_form=register_form, error=register_form.errors)

# <-- LOGIN -->
class User(UserMixin):
    def __init__(self, id_, username, password_hash):
        self.id = id_
        self.username = username.lower()
        self.password_hash = password_hash

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user with ID: {user_id}")
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, password FROM users WHERE id = :id", {'id': int(user_id)})
            row = cursor.fetchone()
            if row:
                print(f"User loaded: {row[1]}")
                return User(id_=row[0], username=row[1], password_hash=row[2])
            print("No user found")
            return None
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Error loading user: {error.message}")
        return None
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, password FROM users WHERE LOWER(username) = :username", {'username': username.lower()})
                row = cursor.fetchone()
                if row:
                    print(f"User found: {row[1]}, Hash: {row[2]}")
                    if check_password_hash(row[2], password):
                        print("Password match")
                        user = User(id_=row[0], username=row[1], password_hash=row[2])
                        login_user(user)
                        return redirect(url_for('home'))
                    else:
                        print("Password mismatch")
                        return render_template('login.html', login_form=login_form, error="Incorrect password")
                else:
                    print(f"No user found for username: {username}")
                    return render_template('login.html', login_form=login_form, error="Username not found")
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            return render_template('login.html', login_form=login_form, error=f"Database error: {error.message}")
        except Exception as e:
            return render_template('login.html', login_form=login_form, error=str(e))
    return render_template('login.html', login_form=login_form, error=login_form.errors)

# <-- LOGOUT -->
@app.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')

#<--- HOME --->
@app.route('/home')
@login_required
def home():
    """Serves the main UI"""
    return render_template('index.html')

#<--- UPLOAD_PAGE --->
@app.route('/upload_page', endpoint='upload_page')
@login_required
def upload():
    """Serves the main UI"""
    return render_template('upload.html')

#<-- UPLOAD_FILES -->
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handles file upload and stores it in the database."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    file_name = file.filename.strip().lower()
    file_type = file.content_type
    file_content = file.read()
    uploaded_by = current_user.id

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            blob_var = cursor.var(cx_Oracle.BLOB)
            cursor.execute(
                "SELECT COUNT(*) FROM files WHERE file_name = :file_name AND uploaded_by = :uploaded_by",
                {"file_name": file_name, "uploaded_by": uploaded_by}
            )
            file_exists = cursor.fetchone()[0] > 0

            if file_exists:
                cursor.execute("""
                    UPDATE files 
                    SET file_blob = EMPTY_BLOB(), file_type = :file_type, upload_date = CURRENT_TIMESTAMP
                    WHERE file_name = :file_name AND uploaded_by = :uploaded_by
                    RETURNING file_blob INTO :file_blob
                """, {
                    "file_type": file_type,
                    "file_name": file_name,
                    "uploaded_by": uploaded_by,
                    "file_blob": blob_var
                })
            else:
                cursor.execute("""
                    INSERT INTO files (file_name, file_type, file_blob, uploaded_by) 
                    VALUES (:file_name, :file_type, EMPTY_BLOB(), :uploaded_by)
                    RETURNING file_blob INTO :file_blob
                """, {
                    "file_name": file_name,
                    "file_type": file_type,
                    "uploaded_by": uploaded_by,
                    "file_blob": blob_var
                })

            blob_locator = blob_var.getvalue()
            if isinstance(blob_locator, list):
                blob_locator = blob_locator[0]
            if blob_locator is not None:
                blob_locator.write(file_content)

            conn.commit()
            return jsonify({"message": "File uploaded successfully!"}), 200
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# <--- DOWNLOAD FILES --->
@app.route('/download/<file_name>', methods=['GET'])
@login_required
def download_file(file_name):
    """Retrieves a file from the database for the current user and serves it for download."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_blob, file_type FROM files WHERE file_name = :file_name AND uploaded_by = :uploaded_by",
                {"file_name": file_name, "uploaded_by": current_user.id}
            )
            row = cursor.fetchone()
            if row:
                file_blob, file_type = row
                return send_file(io.BytesIO(file_blob.read()), mimetype=file_type, as_attachment=True, download_name=file_name)
            else:
                return jsonify({"error": "File not found or access denied"}), 404
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# <--- DELETE FILE --->
@app.route('/delete/<file_name>', methods=['DELETE'])
@login_required
def delete_file(file_name):
    """Deletes a file from the database for the current user."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM files WHERE file_name = :file_name AND uploaded_by = :uploaded_by",
                {"file_name": file_name, "uploaded_by": current_user.id}
            )
            if cursor.fetchone()[0] == 0:
                return jsonify({"error": "File not found or access denied"}), 404

            cursor.execute(
                "DELETE FROM files WHERE file_name = :file_name AND uploaded_by = :uploaded_by",
                {"file_name": file_name, "uploaded_by": current_user.id}
            )
            conn.commit()
            return jsonify({"message": "File deleted successfully!"}), 200
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# <--- MEDIA PREVIEW --->
@app.route('/preview/<file_name>', methods=['GET'])
@login_required
def preview_file(file_name):
    """Handles video streaming with byte-range support for the current user's file."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_blob, file_type FROM files WHERE file_name = :file_name AND uploaded_by = :uploaded_by",
                {"file_name": file_name, "uploaded_by": current_user.id}
            )
            row = cursor.fetchone()

            if not row:
                return jsonify({"error": "File not found or access denied"}), 404

            file_blob, file_type = row
            file_bytes = io.BytesIO(file_blob.read())

            range_header = request.headers.get("Range")
            file_size = len(file_bytes.getvalue())

            if range_header:
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

            return Response(file_bytes.getvalue(), 200, {"Content-Type": file_type})
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#<-- FILE_PAGE -->
@app.route('/file_page', endpoint='file_page')
@login_required
def files():
    return render_template('files.html')

#<-- LIST_FILES -->
@app.route('/files', methods=['GET'])
@login_required
def list_files():
    """Returns a list of files uploaded by the current user."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT file_name, file_type, upload_date FROM files WHERE uploaded_by = :uploaded_by",
                {"uploaded_by": current_user.id}
            )
            files = cursor.fetchall()

            if not files:
                return jsonify({"message": "No files available"}), 200

            file_list = [
                {"file_name": row[0], "file_type": row[1], "upload_date": row[2].strftime("%Y-%m-%d %H:%M:%S")}
                for row in files
            ]
            return jsonify({"files": file_list}), 200
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return jsonify({"error": f"Database error: {error.message}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5001, debug=True)