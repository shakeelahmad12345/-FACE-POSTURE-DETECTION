import cv2
import time
import mediapipe as mp
import smtplib
import requests
from email.message import EmailMessage

# ================= ESP32 STREAM =================
URL = "http://10.15.12.151/stream"
cap = cv2.VideoCapture(URL)

# ================= AI MODEL =================
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh()

# ================= EMAIL =================
SENDER = "aichatb338@gmail.com"
APP_PASSWORD = "faaizgljfmogmqgv"   # IMPORTANT: no spaces
RECEIVER = "Your_email_address_here"  # CHANGE THIS TO YOUR EMAIL

# ================= ESP32 BUZZER =================
ESP_BUZZER_URL = "http://10.15.12.151/buzzer_on"

# ================= EMAIL FUNCTION =================
def send_email(image_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = "⚠️ Posture Alert"
        msg["From"] = SENDER
        msg["To"] = RECEIVER
        msg.set_content("Bad posture detected.")

        with open(image_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="jpeg",
                filename=image_path
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.ehlo()
            smtp.login(SENDER, APP_PASSWORD.strip())
            smtp.send_message(msg)

        print("📧 Email Sent")

    except Exception as e:
        print("Email Error:", e)

# ================= BUZZER =================
def trigger_buzzer():
    try:
        requests.get(ESP_BUZZER_URL, timeout=2)
        print("🔊 Buzzer ON")
    except Exception as e:
        print("Buzzer Error:", e)

# ================= CONTROL =================
alert_sent = False
cooldown = 5
last_alert_time = 0

print("🚀 Posture AI System Started")

# ================= MAIN LOOP =================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera not connected")
        break

    frame = cv2.resize(frame, (640, 480))
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    posture_bad = False

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            h, w, _ = frame.shape

            left_eye = face_landmarks.landmark[33]
            right_eye = face_landmarks.landmark[263]

            x1, y1 = int(left_eye.x * w), int(left_eye.y * h)
            x2, y2 = int(right_eye.x * w), int(right_eye.y * h)

            angle_diff = abs(y1 - y2)

            if angle_diff > 20:
                posture_bad = True

            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # ================= ALERT SYSTEM =================
    if posture_bad and not alert_sent and (time.time() - last_alert_time > cooldown):

        filename = f"posture_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)

        print("🚨 BAD POSTURE DETECTED")

        send_email(filename)
        trigger_buzzer()

        alert_sent = True
        last_alert_time = time.time()

    if not posture_bad:
        alert_sent = False

    # ================= UI =================
    text = "BAD POSTURE" if posture_bad else "GOOD POSTURE"
    color = (0, 0, 255) if posture_bad else (0, 255, 0)

    cv2.putText(frame, text, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("Posture AI System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()