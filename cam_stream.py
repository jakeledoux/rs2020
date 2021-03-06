from lib.iolib import *
from lib import camlib
import socket
import time

# Global variables
HOST = '0.0.0.0'
PORT = get_kwarg('port', 1984)
DELIMITER = b'\n</ts>'
IMG_DELIMITER = b'</img>'
JPG_QUALITY = get_kwarg('quality', 50)
IMG_SCALE = get_kwarg('scale', 1)
TIMEOUT = get_kwarg('timeout', 5)
PYGAME = get_kwarg('pygame', False)

role = get_command(0)
if role:
    # The server will recieve and view the image stream
    if role == 'server':
        print('Listening on {}:{}'.format(HOST, PORT))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, PORT))
            sock.settimeout(TIMEOUT)
            sock.listen()
            conn, addr = sock.accept()
            with conn:
                frame_times = list()
                buffer = b''
                print('Connection established with {}:{}'.format(*addr))
                while True:
                    data = conn.recv(4096)
                    if data:
                        buffer += data
                    else:
                        print('Connection terminated')
                        break
                    if DELIMITER in buffer:
                        *frames, buffer = buffer.split(DELIMITER)
                        frame, timestamp = frames[-1].split(IMG_DELIMITER)
                        # Log frame processed timestamps
                        frame_times.append(time.time())
                        img = camlib.decode_jpg_bytes(frame)
                        camlib.show_frame(img)
                        # Calculate framerate
                        if len(frame_times) >= 13:
                            duration = frame_times[-1] - frame_times[0]
                            print('Current framerate: {}'.format(
                                round(1 / (duration / len(frame_times)))
                            ))
                            print('Current latency: {}'.format(
                                time.time() - float(timestamp)
                            ))
                            frame_times = list()
    # The client will capture and transmit the image stream
    elif role == 'client':
        address = get_command(1)
        if address:
            print('Attempting connection to {}:{}'.format(address, PORT))
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(TIMEOUT)
                sock.connect((address, PORT))
                print('Connection established with {}:{}'.format(address, PORT))
                while True:
                    try:
                        if PYGAME:
                            frame = camlib.get_frame_pygame()
                        else:
                            frame = camlib.get_frame()
                            if frame is None:
                                continue
                        frame = camlib.encode_jpg_bytes(frame, JPG_QUALITY,
                                                        scale=IMG_SCALE)
                        timestamp = str(time.time()).encode()
                        sock.sendall(frame + IMG_DELIMITER + timestamp + DELIMITER)
                    except (ConnectionResetError, BrokenPipeError):
                        print('Connection terminated')
                        break
        else:
            print('No server address specified')
    else:
        print('Invalid role')
else:
    print('Must specify role (server|client)')
