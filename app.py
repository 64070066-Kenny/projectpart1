import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import subprocess


UPLOAD_FOLDER = 'static/uploads/'
RESULT_FOLDER = 'static/results/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def increment_path(path, exist_ok=False):
    """Increment path, i.e. runs/exp --> runs/exp{n}"""
    path = Path(path)
    if (path.exists() and not exist_ok) or (path.with_suffix('').exists() and not exist_ok):
        for n in range(1, 9999):
            p = f"{path}{n}"
            if not Path(p).exists():
                return Path(p)
    return path

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Create a unique result directory
            result_dir = increment_path(Path(app.config['RESULT_FOLDER']) / 'exp')
            os.makedirs(result_dir, exist_ok=True)
            
            # Run the detection script
            command = [
                'python', 'detect.py',
                '--img', '1280',
                '--conf', '0.1',
                '--device', 'cpu',
                '--weights', 'runs/train/exp/weights/best.pt',
                '--source', file_path,
                '--project', str(result_dir.parent),
                '--name', result_dir.name,
                '--exist-ok'
            ]
            subprocess.run(command)
            
            # Get the path to the latest detection result
            result_img = next(result_dir.glob('*.jpg'))

            return redirect(url_for('uploaded_file', result_folder=result_dir.name, filename=result_img.name))
    return render_template('index.html')

@app.route('/results/<result_folder>/<filename>')
def send_result_file(result_folder, filename):
    return send_from_directory(os.path.join(app.config['RESULT_FOLDER'], result_folder), filename)

@app.route('/show/<result_folder>/<filename>')
def uploaded_file(result_folder, filename):
    return render_template('result.html', result_folder=result_folder, filename=filename)

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=8081)
