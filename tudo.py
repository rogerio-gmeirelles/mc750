from pygame import mixer
from time import sleep
import cv2, serial


__FACES__ = -1
__LEDRG__ = -1

def find_faces(webcam):
    global __FACES__

    try:
        ret, image = webcam.read()                                      #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)          # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)     # find faces in the image

    if __FACES__ < 0: return len(faces)                                 # return faces quantity
    else: return __FACES__

def led_status():
    global board, serial, __LEDRG

    if board.in_waiting:                      # Se houver novas entradas
        serial = board.read(board.in_waiting) # Le todas as novas entradas

    if __LEDRG__ < 0: return serial[-1]       # Retorna cor mais recente do led
    else: return __LEDRG__

def sync_audio():
    global AUDIO_DELAY, VIDEO_DELAY, DELAY, base_time, audio_length, frame_count

    DELAY = VIDEO_DELAY
    frame_time = (mixer.music.get_pos()/1000) + base_time  # get audio time for frame
    delay = frame_time - (frame_count*audio_length/9066)

    if abs(delay) > AUDIO_DELAY: print('SYNC|| frame: ', frame_count, ' | delay: ', delay)

    if delay < -1*AUDIO_DELAY:
        sleep(abs(delay))
    elif delay > AUDIO_DELAY:
        DELAY = 1


    return frame_time


def audio_speed(audio_buffer, faces_amount):
    global VIDEO_DELAY, SCAN_FACES, buffer_speed, base_time, audio_length, skip_frame

    if faces_amount <= 1:
        VIDEO_DELAY = 43
        SCAN_FACES = 7
        multiplier = buffer_speed/1
        buffer_speed = 1
        audio_length = 453
        mixer.music.load('deep_time.ogg')
    elif faces_amount == 2:
        VIDEO_DELAY = 32
        SCAN_FACES = 30
        multiplier = buffer_speed/1.2
        buffer_speed = 1.2
        audio_length = 377
        mixer.music.load('deep_time_x12.ogg')
    elif faces_amount == 3:
        VIDEO_DELAY = 31
        SCAN_FACES = 30
        multiplier = buffer_speed/1.4
        buffer_speed = 1.4
        audio_length = 323
        mixer.music.load('deep_time_x14.ogg')
    else:
        VIDEO_DELAY = 20
        SCAN_FACES = 30
        multiplier = buffer_speed/1.6
        buffer_speed = 1.6
        audio_length = 283
        mixer.music.load('deep_time_x16.ogg')


    for time in audio_buffer: time *= multiplier

    base_time = (mixer.music.get_pos()/1000 + base_time)*multiplier

    return base_time

def rewind_video(video_buffer, webcam):
    global DELAY, frame_count, divider
    print("Rewinding")

    mixer.music.stop() # stops audio playback

    i = 0
    for index, frame in enumerate(reversed(video_buffer)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # to greyscale
        displayObservers(gray, 0, -1.0)
        cv2.imshow('frame',gray)                        # show the frame frame
        frame_count -= 1
        # if the face comes back stop rewinding
        if (i % 5) == 4:
            if find_faces(webcam) > 0 or led_status():
                return index

        i += 1                                          # add to the counter
        cv2.waitKey(DELAY)               # wait for 25ms

    return -1       # If surpasses buffer length, return to FRAME_0

def unrewind_video(rewid_buffer, audio_buffer, index, facs_amount):
    global DELAY, SCAN_FACES, MAX_REWIND, base_time, led, frame_count, buffer_speed
    print("Unrewinding")
    buffer_cut = rewind_buffer[len(rewind_buffer)-index:]
    base_time = audio_buffer[len(rewind_buffer)-index]
    mixer.music.play(0, base_time)

    i = 0;
    for frame in buffer_cut:
        i += 1
        if i == SCAN_FACES:
            find_faces(webcam)
            led = led_status()

        sync_audio()
        frame_count += 1

        displayObservers(frame, faces_amount, buffer_speed)
        cv2.imshow('frame',frame)                       # show the frame frame
        cv2.waitKey(DELAY)                              # wait for 25ms

    return

def play_video(rewind_buffer, video, audio_buffer, faces_amount):
    global mute, DELAY, SCAN_FACES, old_faces_amount, frame_count, divider

    frame_count += 1          # update frames amount
    ret, frame = video.read() # get next frame
    frame_time = sync_audio() # make sure audio is sychronized

    if mute:
       mixer.music.play()
       mute = 0

    # updates audio and video buffers
    frame_copy = frame.copy()
    rewind_buffer.append(frame_copy)
    audio_buffer.append(frame_time)

    # check buffers for max capacity
    if len(rewind_buffer) > MAX_REWIND:
        rewind_buffer.pop(0)
        audio_buffer.pop(0)

    if not (old_faces_amount == faces_amount):
        mixer.music.play(0, audio_speed(audio_buffer, faces_amount))
        old_faces_amount = faces_amount

    displayObservers(frame, faces_amount, buffer_speed)
    cv2.imshow('frame',frame)               # show the frame
    cv2.waitKey(DELAY)

def displayObservers(frame, observers, speed):
    frame_copy = frame.copy()
    if speed > 0 and observers == 0:
        observers = 1
    text = "OBSERVERS: " + str(observers) + " (x" + str(float(speed)) + ")"
    cv2.putText(frame_copy, text, (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0))
    return frame_copy

face_cascade = cv2.CascadeClassifier("cascade_face.xml") # Open the Haar Cascade
webcam = cv2.VideoCapture(0) # Open webcam
video = cv2.VideoCapture('deep_time_20fps.mp4') # Open video
board = serial.Serial('COM3', 115200)

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened() and board.is_open:
    continue

# Globals
MAX_REWIND = 300            # Max frames in rewind buffer
VIDEO_DELAY = 43
AUDIO_DELAY = 0.1
DELAY = 43
SCAN_FACES = 7
FRAME_SKIP = 30
serial = [0]
led = 1

rewind_buffer = []
faces_amount = 0
old_faces_amount = 0
frame_count = 0
skip_frame = 3
divider = 1
# thumb = cv2.imread('thumb.png', cv2.IMREAD_COLOR)

# Guarda o momento do audio correspondente ao frame do buffer
audio_buffer = []
audio_length = 453
buffer_speed = 1
base_time = 0
mute = 1
i = 0

# Inicializa modulo e carrega arquivo de som
mixer.init()
mixer.music.load('deep_time.ogg')

while True:
    # Until find faces or led is green
    while faces_amount == 0 and not led_status():
        faces_amount = find_faces(webcam)
        sleep(0.2)

    # Play the video while there are faces
    while (faces_amount > 0 or led):
        for _ in range(SCAN_FACES):
            play_video(rewind_buffer, video, audio_buffer, faces_amount)
        play_video(rewind_buffer, video, audio_buffer, faces_amount)
        led = led_status()
        faces_amount = find_faces(webcam)

    # if the faces disappear, rewind video
    index = 0
    if index >= 0 and not led:
        index = rewind_video(rewind_buffer, webcam)

    #TODO When we run out of buffer go back to the main loop
    if (index > 0 or led):
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer, audio_buffer, index, find_faces(webcam))
        continue
    else:
        rewind_buffer = []
        audio_buffer = []
        buffer_speed = 1
        base_time = 0
        led = 1
        mute = 1
        mixer.music.load('deep_time.ogg')
        video.release()
        video = cv2.VideoCapture('deep_time.mp4')


webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
