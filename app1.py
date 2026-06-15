from flask import Flask, Response, render_template, redirect
import cv2
from datetime import datetime
import csv
import os

capture_time = ""
user_name = "Guest User"

app = Flask(__name__)

current_frame = None
last_image = None

camera = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

def generate_frames():
    global current_frame

    while True:
        success, frame = camera.read()

        if not success:
            break

        current_frame = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )

        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

def save_to_csv(user, time,):

    file_exists = os.path.isfile("scan_history.csv")

    with open(
        "scan_history.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "User",
                "Scan Time",
                
            ])

        writer.writerow([
            user,
            time,
            last_image
        ])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/capture', methods=['POST'])
def capture():

    global current_frame
    global last_image
    global capture_time
    

    if current_frame is not None:

        filename = "captured_face.jpg"

        cv2.imwrite(
            f"static/{filename}",
            current_frame
        )

        last_image = filename

        capture_time = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        save_to_csv(
            user_name,
            capture_time,
        )


    return redirect('/result')

@app.route('/result')
def result():

    return render_template(
        'result.html',
        image=last_image,
        user=user_name,
        time=capture_time,
        
    )

if __name__ == '__main__':
    app.run(debug=True)

