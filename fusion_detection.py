import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import os
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

# 아두이노 시리얼 포트 연결
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # 연결 안정화

# 사용자 콜백 클래스 정의
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.close_detected_time = None  # close 시작 시간

# 콜백 함수 정의
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()

    format, width, height = get_caps_from_pad(pad)
    frame = None
    if user_data.use_frame and format and width and height:
        frame = get_numpy_from_buffer(buffer, format, width, height)

    # detection 결과 확인
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    close_detected = False
    for det in detections:
        label = det.get_label()
        if label == "close":
            close_detected = True
            break

    now = time.time()
    should_trigger = False

    # close가 2초 이상 지속되는지 확인
    if close_detected:
        if user_data.close_detected_time is None:
            user_data.close_detected_time = now
    else:
        user_data.close_detected_time = None

    if user_data.close_detected_time:
        elapsed = now - user_data.close_detected_time
        if elapsed >= 2.0:
            # 아두이노가 출력 중인 CO2 값을 읽음
            arduino.reset_input_buffer()
            time.sleep(0.1)
            try:
                line = arduino.readline().decode().strip()
                if line.startswith("CO2:"):
                    co2_val = int(line.split(":")[1].strip())
                    print(f"[라즈베리파이] 수신된 CO2 값: {co2_val}")
                    if co2_val >= 2000:
                        should_trigger = True
            except Exception as e:
                print("[라즈베리파이] CO2 파싱 오류:", e)

    # 아두이노로 제어 신호 전송
    try:
        if should_trigger:
            arduino.write(b'1')
            print("[라즈베리파이] 경보 조건 충족 → '1' 전송")
        else:
            arduino.write(b'0')
    except Exception as e:
        print("[라즈베리파이] 아두이노 전송 오류:", e)

    # 프레임에 디버깅 텍스트 표시 (선택 사항)
    if user_data.use_frame and frame is not None:
        cv2.putText(frame, f"Close: {close_detected}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if user_data.close_detected_time:
            dur = time.time() - user_data.close_detected_time
            cv2.putText(frame, f"Duration: {dur:.1f}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    return Gst.PadProbeReturn.OK

# 메인 실행
if __name__ == "__main__":
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
