import cv2

cap_width = 640
cap_height = 480

try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_height)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cap_width)
except:
    cap = cv2.VideoCapture(
        f"v4l2src device=/dev/video{0} ! video/x-raw, width={cap_width}, height={cap_height} ! videoconvert ! video/x-raw, format=BGR ! appsink")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('cam', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
