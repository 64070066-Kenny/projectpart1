import os
from flask import Flask, jsonify, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import subprocess
import requests
import traceback
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
RESULT_FOLDER = 'static/results/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
line_bot_api = LineBotApi('')
handler = WebhookHandler('')


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


@app.route("/callback", methods=['POST'])
def callback():
    # Get request headers
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature. Please check your channel access token/channel secret.', 400

    return 'OK', 200

# Function to handle text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.message.text.lower() == "cookie":
        reply_message = TextSendMessage(text="OK")
        line_bot_api.reply_message(event.reply_token, reply_message)



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
                '--conf', '0.5',
                '--device', 'cpu',
                '--weights', 'runs/train/exp/weights/best.pt',
                '--source', file_path,
                '--project', str(result_dir.parent),
                '--name', result_dir.name,
                '--exist-ok',
                '--save-txt',
                '--save-conf',  
            ]
            subprocess.run(command)
            
            # Debugging: Check if result_dir contains .jpg files
            print(f"Result directory: {result_dir}")
            jpg_files = list(result_dir.glob('*.jpg'))
            print(f"Found .jpg files: {jpg_files}")
            if not jpg_files:
                return f"No result images found in {result_dir}"
            
            result_img = jpg_files[0]  # Get the first image
            return redirect(url_for('uploaded_file', result_folder=result_dir.name, filename=result_img.name))
    return render_template('index.html')

@app.route('/results/<result_folder>/<filename>')
def send_result_file(result_folder, filename):
    return send_from_directory(os.path.join(app.config['RESULT_FOLDER'], result_folder), filename)

@app.route('/show/<result_folder>/<filename>')
def uploaded_file(result_folder, filename):
    # Path to the image
    image_path = os.path.join(app.config['RESULT_FOLDER'], result_folder, filename)
    
    # Path to the corresponding .txt file in the labels folder
    label_filename = filename.rsplit('.', 1)[0] + '.txt'
    label_path = os.path.join(app.config['RESULT_FOLDER'], result_folder, 'labels', label_filename)
    
    # Read the content of the .txt file
    if os.path.exists(label_path):
        with open(label_path, 'r') as file:
            label_content = file.read()
    else:
        label_content = "No label file found."
    
    return render_template('result.html', image_url=url_for('send_result_file', result_folder=result_folder, filename=filename), label_content=label_content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

