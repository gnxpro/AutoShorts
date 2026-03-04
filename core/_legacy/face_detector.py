import cv2


def detect_face_center_x(video_path):
    """
    Detect first face and return X center coordinate ratio (0.0 - 1.0).
    If no face detected, return 0.5 (center).
    """

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return 0.5

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_frames = min(30, total_frames)

    for _ in range(sample_frames):
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            frame_width = frame.shape[1]

            center_x = x + w / 2
            ratio = center_x / frame_width

            cap.release()
            return ratio

    cap.release()
    return 0.5
