# Capstone-design


source /home/pi/venv/pytorch_env/bin/activate

우리 yolov8s 실행 코드
rpicam-hello -t 0 --post-process-file ~/rpicam-apps/assets/hailo_yolov8_eyes.json --lores-width 640 --lores-height 640 

hef 모델 있는 경로
/usr/share/hailo-models

예제 코드
python3 basic_pipelines/detection.py --labels-json /home/pi/hailo-rpi5-examples/resources/eyes-labels.json --hef-path /usr/share/hailo-models/eyes.hef --input /home/pi/hailo-rpi5-examples/test1.mp4
python3 detection_pipeline2.py   --labels-json ../resources/eyes-labels.json   --hef-path /usr/share/hailo-models/eyes.hef



테스트코드
 python3 detect.py --source 0 --weights best.pt --conf 0.25

전역 패키지 가상환경에서 참조
python3 -m venv /home/pi/venv/pytorch_env --system-site-packages

파이카메라 무기한 출력
rpicam-hello -t 0
---------------------------------------------------------------------------------------------------------------------------------------------------------
************************
cd ~/hailo-rpi5-examples
source setup_env.sh   
thonny

객체인식 헤일로 예제
rpicam-hello -t 0 --post-process-file ~/rpicam-apps/assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640

헤일로 공식 문서 - 가상환경 접속
cd hailo-rpi5-examples
source setup_env.sh

헤일로 예제 실행(우리가 학습시킨 모)
python3 basic_pipelines/detection.py --labels-json resources/eyes-labels.json --hef-path /usr/share/hailo-models/eyes.hef --input rpi

20250122수 프레임 30으로 매우 빠르게 실시간 탐지가 가능. 허나 눈이 바운딩 박스로 탐지가 되지만, bicycle이라고 클래스가 잡히는 오류와, close 부분이 아예 탐지되지 않는 오류가 발생함.
rpicam-hello -t 0 --post-process-file ~/hailo-rpi5-examples/resources/hailo_yolov8_eyes.json --lores-width 640 --lores-height 640




python basic_pipelines/get_usb_camera.py

python basic_pipelines/detection.py --input /dev/video0

기존 가상환경 /home/pi/venv/pytorch_env/bin/python3
라벨링 가상환경 /home/pi/labelme/label/bin/python3
