import os
from PIL import Image
from flask import Flask, flash, request, jsonify, render_template, Response
from flask_cors import CORS
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import numpy as np
from numpy import asarray
import tensorflow as tf
import cv2
from skimage.transform import resize
import datetime

global capture, switch, name_class, confidence_score
capture = 0
switch = 0
name_class = ""
confidence_score = ""

load_dotenv()

MODEL = tf.keras.models.load_model("model/3")
CLASS_NAMES = ["Hạt khiếm khuyết- Defect", "Hạt dài - Longberry", "Hạt tròn - Peaberry", "Hạt thượng hạng - Premium"]

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, template_folder='./templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# camera = cv2.VideoCapture(0)
global start_camera
start_camera = 0

CORS(app)   # Cross-origin resource sharing

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_array):
    # Resize the array to (256, 256)
    # resized_image = resize(image_array, (256, 256, image_array.shape[2]), mode='reflect', anti_aliasing=True)
    # resized_image = image_array.resize((256, 256), Image.ANTIALIAS)
    # return resized_image
    img = Image.fromarray(image_array)
    resized_image = img.resize((256, 256), Image.ANTIALIAS)
    return np.asarray(resized_image)

def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return "Not a file"
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return "empty file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        return "file invalid"
    return filename

def convert_from_bytes_to_numpyarray(filename):
    img = Image.open(UPLOAD_FOLDER+"\\"+filename)
    # asarray() class is used to convert
    # PIL images into NumPy arrays
    numpydata = asarray(img)
    return numpydata

@app.route("/predict",methods=["POST"])
def Predict(img=""):
    switch = 0
    if img != "":
        file_name = img
        switch = 1
    else:
        file_name = upload_file()
    # convert from [256,256,3] -> [[256,256,3]]
    img = convert_from_bytes_to_numpyarray(file_name)
    img = resize_image(img)
    img_batch = np.expand_dims(img, 0)
    predictions = MODEL.predict(img_batch)
    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])
    data = [{
        'class': predicted_class,
        'confidence': round(float(confidence),4)
    }]
    print(data)
    if switch :
        return data
    resp = jsonify(data=data)
    return resp

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():  # generate frame by frame from camera
    global capture
    while True:
        if start_camera == 0:
            break
        success, frame = camera.read() 
        if success:   
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['uploads', "shot_{}.jpg".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame) 
                file_name = p[8:]
                with app.app_context(), app.test_request_context():
                    data = Predict(file_name)
                    global name_class, confidence_score
                    name_class = data[0]['class']
                    confidence_score = data[0]['confidence']
                    break

            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass       
        else:
            break

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1 
        elif  request.form.get('stop') == 'Stop/Start':
            if(switch==1):
                switch=0
                global name_class, confidence_score
                name_class = ""
                confidence_score = ""
                camera.release()
                cv2.destroyAllWindows() 
            else:
                global start_camera
                start_camera = 1
                camera = cv2.VideoCapture(0)
                switch=1
    elif request.method=='GET':
        return render_template('home.html',name_class=name_class,confidence_score=confidence_score)         
    return render_template('home.html',name_class=name_class,confidence_score=confidence_score)


@app.route("/home",methods=["GET"])
def Home():
    return render_template('home.html',name=name_class,confidence_score=confidence_score)

if __name__ == "__main__":
    #Run the app in the application context
    with app.app_context():
        app.run(debug=True)

# camera.release()
# cv2.destroyAllWindows()  