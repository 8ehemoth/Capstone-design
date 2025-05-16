import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import time
import serial
import cv2
import numpy as np
import hailo

from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp

# 1. 아두이노 시리얼 연결
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

# 2. 사용자 콜백 클래스 정의
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()

# 3. GStreamer 콜백 함수
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    format, width, height = get_caps_from_pad(pad)
    frame = None
    if user_data.use_frame and format and width and height:
        frame = get_numpy_from_buffer(buffer, format, width, height)

    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    labels = [det.get_label() for det in detections]

    close_detected = "close" in labels
    open_detected = "open" in labels

    # 아두이노로 전송
    try:
        if close_detected:
            arduino.write(b'1')
            print("[알람] 'close' 감지 → '1' 전송")
        elif open_detected:
            arduino.write(b'0')
            print("[해제] 'open' 감지 → '0' 전송")
        else:
            arduino.write(b'0')
    except Exception as e:
        print("[Serial] 아두이노 전송 오류:", e)

    # 디버깅 텍스트
    if user_data.use_frame and frame is not None:
        cv2.putText(frame, f"Labels: {', '.join(labels)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    return Gst.PadProbeReturn.OK

# 4. 앱 실행
if __name__ == "__main__":
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
