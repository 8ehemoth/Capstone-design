import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import time
import serial
import threading
import cv2
import numpy as np
import hailo

from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp

# 1. 아두이노 시리얼 연결 설정
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

# 2. 전역 CO2 상태 공유 변수
latest_co2 = 0

# 3. CO2 수신용 스레드
def read_co2_loop():
    global latest_co2
    while True:
        try:
            line = arduino.readline().decode().strip()
            if line.startswith("CO2:"):
                co2_val = int(line.split(":")[1].strip())
                latest_co2 = co2_val
                print(f"[CO2] 현재 농도: {co2_val} ppm")
        except Exception as e:
            print("[CO2] 읽기 오류:", e)
        time.sleep(0.1)

threading.Thread(target=read_co2_loop, daemon=True).start()

# 4. 사용자 콜백 클래스 정의
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.close_detected_time = None

# 5. GStreamer 콜백 함수
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

    # 'close' 탐지 확인
    close_detected = any(det.get_label() == "close" for det in detections)

    now = time.time()
    should_trigger = False

    if close_detected:
        if user_data.close_detected_time is None:
            user_data.close_detected_time = now
    else:
        user_data.close_detected_time = None

    # 2초 이상 + CO2 조건 만족 시 트리거
    if user_data.close_detected_time:
        elapsed = now - user_data.close_detected_time
        if elapsed >= 2.0 and latest_co2 >= 2000:
            should_trigger = True

    try:
        if should_trigger:
            arduino.write(b'1')
            print("[알람] 조건 만족 → '1' 전송")
        else:
            arduino.write(b'0')
    except Exception as e:
        print("[Serial] 전송 오류:", e)

    # 디버깅 텍스트 출력
    if user_data.use_frame and frame is not None:
        cv2.putText(frame, f"Close: {close_detected}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if user_data.close_detected_time:
            dur = now - user_data.close_detected_time
            cv2.putText(frame, f"Duration: {dur:.1f}s", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"CO2: {latest_co2}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    return Gst.PadProbeReturn.OK

# 6. 앱 실행
if __name__ == "__main__":
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
