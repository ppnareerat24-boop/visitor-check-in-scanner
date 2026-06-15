from flask import Flask, Response, render_template, redirect, request
import cv2
from datetime import datetime
import csv
import os
import time

face_detected_time = None
auto_capture = False
capture_completed = False
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
    global last_image
    global capture_time
    global face_detected_time
    global auto_capture
    global capture_completed

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
                (0,255,0),
                2
            )


        if len(faces) > 0 and not capture_completed:

            if face_detected_time is None:
                face_detected_time = time.time()

            elapsed = time.time() - face_detected_time

            countdown = max(
                0,
                3 - int(elapsed)
            )

            cv2.putText(
                frame,
                f"Capture in {countdown}",
                (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255),
                2
            )

            if elapsed >= 3:

                filename = datetime.now().strftime(
                    "face_%Y%m%d_%H%M%S_%f.jpg"
                )

                cv2.imwrite(
                    f"static/{filename}",
                    current_frame
                )

                last_image = filename

                capture_time = datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

                capture_completed = True

                cv2.putText(
                    frame,
                    "Captured!",
                    (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2
                )

        else:

            face_detected_time = None


        ret, buffer = cv2.imencode(
            ".jpg",
            frame
        )

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

    

def save_to_csv(user, role, reason, time, image):
    file_exists = os.path.isfile("scan_history.csv")
    with open("scan_history.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Role", "Reason", "Scan Time", "Image"])
        writer.writerow([user, role, reason, time, image])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/capture_status')
def capture_status():

    global capture_completed

    if capture_completed:
        return "done"

    return "waiting"


@app.route('/capture', methods=['POST'])
def capture():
    global current_frame, last_image, capture_time
    if current_frame is not None:
        filename = datetime.now().strftime(
            "face_%Y%m%d_%H%M%S_%f.jpg"
        )
        cv2.imwrite(f"static/{filename}", current_frame)
        last_image = filename
        capture_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return redirect('/register')

@app.route('/register')
def register():
    return render_template('register.html', image=last_image, time=capture_time)

@app.route('/submit', methods=['POST'])
def submit():
    global user_name
    name = request.form.get('name')
    role = request.form.get('role')
    reason = request.form.get('reason')
    user_name = name
    save_to_csv(name, role, reason, capture_time, last_image)
    return redirect('/result')

@app.route('/result')
def result():
    return render_template('result.html', image=last_image, user=user_name, time=capture_time)

@app.route('/history')
def history():

    history_data = []

    try:
        with open(
            "scan_history.csv",
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                history_data.append(row)

    except FileNotFoundError:
        pass

    return render_template(
        "history.html",
        history=history_data
    )

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        camera.release()
        cv2.destroyAllWindows()