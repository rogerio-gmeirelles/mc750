import RPi.GPIO as GPIO
import numpy as np
import cv2
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN)
has_observer = False
# setup callbacks for when GPIO22 is:
#    HIGH - an observer was detected
#    LOW  - an observer left
def has_observer_true():
    has_observer = True
def has_observer_false():
    has_observer = False
GPIO.add_event_detect(22, GPIO.RISING,  callback=has_observer_true)
GPIO.add_event_detect(22, GPIO.FALLING, callback=has_observer_false)

# Const
MAX_REWIND = 300 # Max amount of frames in the rewind buffer
DELAY      = 25
DELAY_MIN  = 15
VIDEO_FILE = 'Britney Spears - ...Baby One More Time.mp4'

def find_faces(webcam):
    try:
        ret, image = webcam.read()                                   # capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)       # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)  # find faces in the image
    return len(faces)                                                # return the amount of faces detected

def rewind_video(buffer, webcam):
    print("Rewinding")
    i = 0
    for index, frame in enumerate(reversed(buffer)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # to greyscale
        cv2.imshow('frame', gray)                       # show the frame frame
        # if the face comes back stop rewinding
        if (i % 10) == 9:
            if find_faces(webcam) > 0:
                return index
            else:
                cv2.waitKey(DELAY_MIN)
        i += 1                                          # add to the counter
        cv2.waitKey(DELAY)                              # wait for 25ms
    return -1

def unrewind_video(buffer, index):
    print("Unrewinding")
    buffer_cut = buffer[MAX_REWIND-index:]
    for frame in buffer_cut:
        cv2.imshow('frame', frame)                      # show the frame frame
        cv2.waitKey(DELAY)                              # wait for 25ms

def play_video(faces_amount, rewind_buffer, video, delay=DELAY):
    ret, frame = video.read()                           # get next frame
    # mantem o rewind buffer
    rewind_buffer.append(frame)
    if len(rewind_buffer) > MAX_REWIND:
        rewind_buffer.pop(0)

    cv2.putText(img=frame, text=str(faces_amount), org=(10,500), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255, 255, 255))

    cv2.imshow('frame', frame)                          # show the frame
    cv2.waitKey(delay)                                  # wait for 25ms


# Open the Haar Cascade
face_cascade = cv2.CascadeClassifier("cascade_face.xml")
# Open webcam
webcam = cv2.VideoCapture(0)
# Open video
video = cv2.VideoCapture(VIDEO_FILE)

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened():
    continue

ret, frame = video.read()
FRAME_0 = frame # First frame

# Vars
# rewinding = False
rewind_buffer = []
faces_amount = 0

while True:
    # Stay on the first frame
    cv2.imshow('frame', FRAME_0)

    # Until faces are found
    while faces_amount == 0:
        faces_amount = find_faces(webcam)
        sleep(0.5)

    # Play the video while there are faces detected or observers
    while faces_amount > 0 or has_observer:
        for _ in range(10):
            play_video(faces_amount, rewind_buffer, video)
        play_video(faces_amount, rewind_buffer, video, DELAY_MIN)
        faces_amount = find_faces(webcam)

    # If the faces disappear and no observer is detected, rewind video
    index = rewind_video(rewind_buffer, webcam)

    # TODO When we run out of buffer go back to the main loop
    if index > 0:
        # Replay what was rewinded if the observer returned
        unrewind_video(rewind_buffer, index)
        continue
    else:
        rewind_buffer = []
        video.release()
        video = cv2.VideoCapture(VIDEO_FILE)

webcam.release()
video.release()
cv2.destroyAllWindows()
