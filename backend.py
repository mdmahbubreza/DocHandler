from flask import Flask, request, jsonify, send_file, render_template
import os
from werkzeug.utils import secure_filename
from PIL import Image  # For image compression
import zipfile         # For general file compression

app = Flask(__name__)

# Configure file upload paths
UPLOAD_FOLDER = './uploads'
COMPRESSED_FOLDER = './compressed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# Allowed file types for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'zip', 'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Compress Image to Target Size
def compress_image(input_path, output_path, target_size_kb):
    with Image.open(input_path) as img:
        quality = 95  # Start with high quality
        while os.path.getsize(input_path) > target_size_kb * 1024 and quality > 10:
            img.save(output_path, "JPEG", quality=quality)
            quality -= 5
        return output_path if os.path.getsize(output_path) <= target_size_kb * 1024 else None

@app.route('/')
def home():
    return render_template('index.html')  # Serve the frontend

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    target_size_kb = int(request.form.get('target_size_kb', 100))  # Get target size from form

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Compress file based on type
        compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
        if filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}:
            compressed_file = compress_image(input_path, compressed_path, target_size_kb)
        else:
            # Example for generic file compression using zip
            compressed_file = compressed_path + '.zip'
            with zipfile.ZipFile(compressed_file, 'w') as zipf:
                zipf.write(input_path, arcname=filename)

        if compressed_file and os.path.exists(compressed_file):
            return jsonify({'success': True, 'download_url': f'/download/{os.path.basename(compressed_file)}'})
        else:
            return jsonify({'error': 'Could not compress file to the required size'}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
