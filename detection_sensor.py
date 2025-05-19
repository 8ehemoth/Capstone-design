#!/usr/bin/env python3
"""
detection_sensor.py
  · 기존 detection_simple 파이프라인 + Arduino 알람 제어
  · 눈(label == "close")이 15 프레임 연속 → 아두이노 ‘1’ 전송
  · CO2:#### 값이 2000 ppm 이상 수신되면 즉시 ‘1’
  · 그 외에는 ‘0’
"""
import gi, time, serial, threading, queue, hailo
gi.require_version('Gst', '1.0'),
from gi.repository import Gst
from hailo_apps_infra.hailo_rpi_common import app_callback_class
from hailo_apps_infra.detection_pipeline_simple import GStreamerDetectionApp

# ─── Arduino 직렬 초기화 ────────────────────────────────────────────
SER = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)

co2_q = queue.Queue()
def reader():
    """아두이노 → Pi (CO₂) 백그라운드 수신"""
    while True:
        line = SER.readline().decode(errors='ignore').strip()
        if line.startswith("CO2:"):
            try:
                co2 = int(line[4:])
                co2_q.put(co2)
            except ValueError:
                pass
threading.Thread(target=reader, daemon=True).start()

# ─── 사용자 데이터 클래스 ───────────────────────────────────────────
class DrowsyState(app_callback_class):
    def __init__(self, shut_sec=2.0):
        super().__init__()
        self.shut_sec     = shut_sec   # 연속 감긴 시간 한계
        self.shut_start   = None       # 감기 시작 시각 (None = 열려 있음)

# ─── 콜백 함수 ──────────────────────────────────────────────────────
def app_callback(pad, info, user: DrowsyState):
    buf = info.get_buffer()
    if buf is None:
        return Gst.PadProbeReturn.OK

    # 1) 이번 프레임에서 눈이 감겼는지 판정
    eyes_closed = False
    for det in hailo.get_roi_from_buffer(buf).get_objects_typed(hailo.HAILO_DETECTION):
        if det.get_label() == "close" and det.get_confidence() > 0.5:
            eyes_closed = True
            break

    now = time.time()

    # 2) 감김 시간 누적 / 리셋
    if eyes_closed:
        if user.shut_start is None:        # 처음 감겼다
            user.shut_start = now
    else:
        user.shut_start = None             # 다시 열림 → 타이머 리셋

    # 3) 알람 조건 평가
    alarm = False
    if user.shut_start is not None and (now - user.shut_start) >= user.shut_sec:
        alarm = True

    # 4) CO₂ 조건 (그대로 유지)
    try:
        if co2_q.get_nowait() >= 2000:
            alarm = True
    except queue.Empty:
        pass

    # 5) 아두이노로 신호 전송
    SER.write(b'1' if alarm else b'0')
    return Gst.PadProbeReturn.OK

# ─── 메인 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_data = DrowsyState()
    app = GStreamerDetectionApp(app_callback, user_data)   # ← 원본과 동일 호출
    app.run()
