import redis
import serial
import time

# Redis 서버 연결
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# 아두이노 시리얼 포트 설정 (라즈베리파이에 맞게 수정)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

print("센서 제어 모듈 시작됨...")

while True:
    try:
        alert = r.get("alert")
        if alert == b'1':
            print("⚠️  'close' 감지됨 - 센서 작동")
            ser.write(b'1')  # 부저 및 진동 모듈 ON
        else:
            ser.write(b'0')  # 센서 OFF
        time.sleep(0.1)
    except Exception as e:
        print("에러:", e)
        time.sleep(1)
