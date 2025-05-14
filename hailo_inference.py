import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo

# 변경된 모듈 경로
from hailo_apps_infra.utils.parse_args import get_default_parser
from hailo_apps_infra.gst.common.pipeline_elements import (
    SOURCE_PIPELINE,
    DETECTION_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE
)
from hailo_apps_infra.gst.common.gstreamer_app import GStreamerApp
from hailo_apps_infra.gst.common.common import (
    QUEUE,
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
    dummy_callback
)


class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, app_callback, user_data):
        parser = get_default_parser()
        parser.add_argument(
            "--network",
            default="yolov8s_eye",
            choices=['yolov8s_eye'],
            help="Which Network to use, default is yolov8s_eye",
        )
        parser.add_argument(
            "--hef-path",
            default=None,
            help="Path to HEF file",
        )
        parser.add_argument(
            "--labels-json",
            default=None,
            help="Path to custom labels JSON file",
        )
        args = parser.parse_args()

        super().__init__(args, user_data)

        # self.current_path 보완
        self.current_path = os.path.dirname(os.path.realpath(__file__))

        self.batch_size = 2
        self.network_width = 640
        self.network_height = 640
        self.network_format = "RGB"
        nms_score_threshold = 0.3
        nms_iou_threshold = 0.45

        if args.hef_path is not None:
            self.hef_path = args.hef_path
        elif args.network == "yolov8s_eye":
            self.hef_path = os.path.join(self.current_path, 'resources/yolov8s_eye.hef')
        else:
            raise ValueError("Invalid network type")

        self.labels_json = args.labels_json
        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        setproctitle.setproctitle("Hailo Eye Detection App")
        self.create_pipeline()

    def get_pipeline_string(self):
        # 부모 클래스에서 video_source, video_sink 등 초기화되어야 함
        source_pipeline = SOURCE_PIPELINE(self.video_source)
        detection_pipeline = DETECTION_PIPELINE(
            hef_path=self.hef_path,
            batch_size=self.batch_size,
            labels_json=self.labels_json,
            additional_params=self.thresholds_str
        )
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(
            video_sink=self.video_sink,
            sync=self.sync,
            show_fps=self.show_fps
        )
        pipeline_string = (
            f'{source_pipeline} '
            f'{detection_pipeline} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )
        print("Generated pipeline:")
        print(pipeline_string)
        return pipeline_string


if __name__ == "__main__":
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
