"""Multi-Class Vehicle Detection Engine using ONNX Runtime (Module 10).

Provides high-performance multi-class vehicle detection (Car, Motorcycle, Bus, Truck,
Auto-Rickshaw, Van) with letterbox preprocessing, IoU Non-Maximum Suppression (NMS),
coordinate normalization, vehicle crop extraction, and synthetic fallback for headless CI/CD.
"""

import logging
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.schemas.detection import (
    BoundingBox,
    DetectedVehicle,
    DetectorConfig,
    DetectorTelemetry,
    FrameDetectionResult,
    VehicleClass,
)
from app.schemas.stream import VideoFrame

logger = logging.getLogger("sentinelx.detector")

# COCO to SentinelX Vehicle Taxonomy Mapping
COCO_VEHICLE_MAP: Dict[int, VehicleClass] = {
    2: VehicleClass.CAR,
    3: VehicleClass.MOTORCYCLE,
    5: VehicleClass.BUS,
    7: VehicleClass.TRUCK,
}


class VehicleDetector:
    """ONNX Runtime based Multi-Class Vehicle Detector."""

    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()
        self._lock = threading.Lock()
        self.session = None
        self.execution_provider = "CPUExecutionProvider"
        self.is_mock = self.config.use_synthetic_detector

        # Telemetry
        self._total_frames: int = 0
        self._total_vehicles: int = 0
        self._latency_samples: deque[float] = deque(maxlen=100)
        self._fps_timestamps: deque[float] = deque(maxlen=50)
        self._class_counts: Dict[str, int] = {vc.value: 0 for vc in VehicleClass}
        self._last_inference_at: Optional[datetime] = None

        self._init_session()

    def _init_session(self) -> None:
        """Initialize ONNX Runtime inference session or fallback to synthetic detector."""
        if self.is_mock or not self.config.model_path or not os.path.exists(self.config.model_path):
            self.is_mock = True
            self.execution_provider = "SyntheticDetector (No ONNX Model Loaded)"
            logger.info("VehicleDetector initialized in SYNTHETIC MOCK mode.")
            return

        try:
            import onnxruntime as ort

            available_providers = ort.get_available_providers()
            preferred_order = [
                "CUDAExecutionProvider",
                "DirectMLExecutionProvider",
                "OpenVINOExecutionProvider",
                "CPUExecutionProvider",
            ]
            providers = [p for p in preferred_order if p in available_providers] or [
                "CPUExecutionProvider"
            ]

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = max(1, os.cpu_count() or 4)

            self.session = ort.InferenceSession(
                self.config.model_path, sess_options=sess_options, providers=providers
            )
            self.execution_provider = self.session.get_providers()[0]
            self.is_mock = False
            logger.info(
                f"Loaded ONNX Vehicle Detection Model from {self.config.model_path} on {self.execution_provider}"
            )
        except Exception as e:
            logger.warning(f"Failed to load ONNX model ({e}). Falling back to synthetic detector.")
            self.is_mock = True
            self.execution_provider = "SyntheticDetector (Fallback)"

    def configure(self, config: DetectorConfig) -> None:
        """Dynamically update detector parameters."""
        with self._lock:
            reinit = (
                config.model_path != self.config.model_path
                or config.use_synthetic_detector != self.config.use_synthetic_detector
            )
            self.config = config
            if reinit:
                self.is_mock = config.use_synthetic_detector
                self._init_session()

    @staticmethod
    def letterbox(
        image: np.ndarray,
        target_shape: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114),
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Resize and pad image preserving aspect ratio for ONNX input."""
        h, w = image.shape[:2]
        target_w, target_h = target_shape

        r = min(target_w / w, target_h / h)
        new_unpad_w, new_unpad_h = int(round(w * r)), int(round(h * r))
        dw, dh = (target_w - new_unpad_w) / 2, (target_h - new_unpad_h) / 2

        if (w, h) != (new_unpad_w, new_unpad_h):
            image = cv2.resize(image, (new_unpad_w, new_unpad_h), interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))

        padded_image = cv2.copyMakeBorder(
            image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        return padded_image, r, (dw, dh)

    @staticmethod
    def nms_boxes(
        boxes: List[Tuple[float, float, float, float]],
        scores: List[float],
        iou_threshold: float = 0.45,
    ) -> List[int]:
        """Perform Non-Maximum Suppression (NMS) over bounding boxes."""
        if not boxes:
            return []

        boxes_arr = np.array(boxes, dtype=np.float32)
        scores_arr = np.array(scores, dtype=np.float32)

        x1 = boxes_arr[:, 0]
        y1 = boxes_arr[:, 1]
        x2 = boxes_arr[:, 2]
        y2 = boxes_arr[:, 3]

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores_arr.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(int(i))

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h

            ovr = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(ovr <= iou_threshold)[0]
            order = order[inds + 1]

        return keep

    @staticmethod
    def extract_vehicle_crop(image: np.ndarray, bbox: BoundingBox) -> Optional[np.ndarray]:
        """Crop the localized vehicle bounding box from the video frame safely."""
        h, w = image.shape[:2]
        x1 = max(0, int(round(bbox.x1)))
        y1 = max(0, int(round(bbox.y1)))
        x2 = min(w, int(round(bbox.x2)))
        y2 = min(h, int(round(bbox.y2)))

        if x2 <= x1 or y2 <= y1 or (x2 - x1) < 10 or (y2 - y1) < 10:
            return None

        return image[y1:y2, x1:x2].copy()

    def _generate_synthetic_detections(
        self,
        camera_id: str,
        frame_idx: int,
        timestamp_utc: datetime,
        width: int,
        height: int,
    ) -> List[DetectedVehicle]:
        """Generate realistic vehicle detections across simulated road lanes for testing."""
        np.random.seed((frame_idx * 17 + hash(camera_id)) % 2147483647)

        # 1 to 3 simulated vehicles in frame
        num_vehicles = int(np.random.choice([1, 2, 3], p=[0.2, 0.5, 0.3]))
        classes = [
            VehicleClass.CAR,
            VehicleClass.MOTORCYCLE,
            VehicleClass.BUS,
            VehicleClass.TRUCK,
            VehicleClass.AUTO_RICKSHAW,
        ]
        active_classes = [c for c in classes if c in self.config.enabled_classes] or [
            VehicleClass.CAR
        ]

        detections: List[DetectedVehicle] = []
        for lane_idx in range(num_vehicles):
            v_class = active_classes[(frame_idx + lane_idx) % len(active_classes)]
            conf = float(np.random.uniform(max(0.65, self.config.confidence_threshold), 0.98))

            # Simulate lane positions
            lane_offset = (lane_idx + 1) / (num_vehicles + 1)
            box_w = float(width * np.random.uniform(0.18, 0.32))
            box_h = float(height * np.random.uniform(0.16, 0.28))
            center_x = float(width * lane_offset + (np.sin(frame_idx * 0.1 + lane_idx) * 20))
            center_y = float(height * 0.55 + (lane_idx * 40))

            x1 = max(0.0, center_x - box_w / 2)
            y1 = max(0.0, center_y - box_h / 2)
            x2 = min(float(width), x1 + box_w)
            y2 = min(float(height), y1 + box_h)

            bbox = BoundingBox(
                x1=round(x1, 2),
                y1=round(y1, 2),
                x2=round(x2, 2),
                y2=round(y2, 2),
                norm_x1=round(x1 / width, 4),
                norm_y1=round(y1 / height, 4),
                norm_x2=round(x2 / width, 4),
                norm_y2=round(y2 / height, 4),
                width=round(x2 - x1, 2),
                height=round(y2 - y1, 2),
            )

            color_est = np.random.choice(["White", "Silver", "Black", "Red", "Blue", "Yellow"])

            detections.append(
                DetectedVehicle(
                    camera_id=camera_id,
                    frame_index=frame_idx,
                    timestamp_utc=timestamp_utc,
                    vehicle_class=v_class,
                    confidence=round(conf, 4),
                    bbox=bbox,
                    has_crop=True,
                    crop_width=int(bbox.width),
                    crop_height=int(bbox.height),
                    color_estimate=str(color_est),
                )
            )

        return detections

    def detect(self, video_frame: VideoFrame) -> FrameDetectionResult:
        """Execute vehicle detection inference on a video frame."""
        start_t = time.perf_counter()
        now_ts = time.time()
        now_utc = video_frame.timestamp_utc or datetime.now(timezone.utc)
        img = video_frame.image
        orig_h, orig_w = img.shape[:2]

        vehicles: List[DetectedVehicle] = []

        if self.is_mock or self.session is None:
            # Synthetic detection path
            time.sleep(0.005)  # Simulate fast 5ms inference
            vehicles = self._generate_synthetic_detections(
                camera_id=video_frame.camera_id,
                frame_idx=video_frame.frame_index,
                timestamp_utc=now_utc,
                width=orig_w,
                height=orig_h,
            )
        else:
            # Real ONNX inference path
            try:
                padded_img, r, (dw, dh) = self.letterbox(
                    img, target_shape=(self.config.input_width, self.config.input_height)
                )
                # Convert BGR to RGB and normalize
                input_tensor = padded_img[:, :, ::-1].transpose(2, 0, 1).astype(np.float32)
                input_tensor = np.ascontiguousarray(input_tensor) / 255.0
                input_tensor = np.expand_dims(input_tensor, axis=0)

                input_name = self.session.get_inputs()[0].name
                outputs = self.session.run(None, {input_name: input_tensor})

                raw_preds = outputs[0]  # Shape: (1, N, num_classes + 5)
                if raw_preds.ndim == 3:
                    raw_preds = raw_preds[0]

                boxes_list: List[Tuple[float, float, float, float]] = []
                scores_list: List[float] = []
                classes_list: List[VehicleClass] = []

                for row in raw_preds:
                    if len(row) < 6:
                        continue
                    cx, cy, w, h = row[0:4]
                    obj_conf = float(row[4])
                    class_scores = row[5:]
                    class_id = int(np.argmax(class_scores))
                    class_conf = float(class_scores[class_id])
                    total_score = obj_conf * class_conf

                    if total_score >= self.config.confidence_threshold:
                        v_class = COCO_VEHICLE_MAP.get(class_id)
                        if v_class and v_class in self.config.enabled_classes:
                            # Convert center-xywh to corners
                            bx1 = cx - w / 2
                            by1 = cy - h / 2
                            bx2 = cx + w / 2
                            by2 = cy + h / 2
                            boxes_list.append((bx1, by1, bx2, by2))
                            scores_list.append(total_score)
                            classes_list.append(v_class)

                # Apply NMS
                keep_indices = self.nms_boxes(
                    boxes_list, scores_list, iou_threshold=self.config.nms_iou_threshold
                )

                for idx in keep_indices:
                    bx1, by1, bx2, by2 = boxes_list[idx]
                    # De-letterbox back to original image
                    x1 = max(0.0, min(float(orig_w), (bx1 - dw) / r))
                    y1 = max(0.0, min(float(orig_h), (by1 - dh) / r))
                    x2 = max(0.0, min(float(orig_w), (bx2 - dw) / r))
                    y2 = max(0.0, min(float(orig_h), (by2 - dh) / r))

                    if x2 > x1 and y2 > y1:
                        bbox = BoundingBox(
                            x1=round(x1, 2),
                            y1=round(y1, 2),
                            x2=round(x2, 2),
                            y2=round(y2, 2),
                            norm_x1=round(x1 / orig_w, 4),
                            norm_y1=round(y1 / orig_h, 4),
                            norm_x2=round(x2 / orig_w, 4),
                            norm_y2=round(y2 / orig_h, 4),
                            width=round(x2 - x1, 2),
                            height=round(y2 - y1, 2),
                        )
                        vehicles.append(
                            DetectedVehicle(
                                camera_id=video_frame.camera_id,
                                frame_index=video_frame.frame_index,
                                timestamp_utc=now_utc,
                                vehicle_class=classes_list[idx],
                                confidence=round(scores_list[idx], 4),
                                bbox=bbox,
                                has_crop=True,
                                crop_width=int(bbox.width),
                                crop_height=int(bbox.height),
                            )
                        )
            except Exception as e:
                logger.error(f"Inference error in VehicleDetector: {e}")

        inference_ms = (time.perf_counter() - start_t) * 1000.0

        # Update Telemetry
        with self._lock:
            self._total_frames += 1
            self._total_vehicles += len(vehicles)
            self._latency_samples.append(inference_ms)
            self._fps_timestamps.append(now_ts)
            self._last_inference_at = now_utc
            for v in vehicles:
                self._class_counts[v.vehicle_class.value] = (
                    self._class_counts.get(v.vehicle_class.value, 0) + 1
                )

        return FrameDetectionResult(
            camera_id=video_frame.camera_id,
            frame_index=video_frame.frame_index,
            timestamp_utc=now_utc,
            inference_time_ms=round(inference_ms, 2),
            total_vehicles=len(vehicles),
            vehicles=vehicles,
        )

    def get_telemetry(self) -> DetectorTelemetry:
        """Retrieve real-time performance and throughput telemetry."""
        with self._lock:
            now = time.time()
            cutoff = now - 3.0
            valid_fps = [t for t in self._fps_timestamps if t >= cutoff]
            fps = len(valid_fps) / 3.0 if valid_fps else 0.0
            avg_latency = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            return DetectorTelemetry(
                model_name=os.path.basename(self.config.model_path)
                if self.config.model_path
                else "YOLOX-ONNX-Per-Class",
                execution_provider=self.execution_provider,
                is_mock=self.is_mock,
                total_frames_processed=self._total_frames,
                total_vehicles_detected=self._total_vehicles,
                average_inference_ms=round(avg_latency, 2),
                inference_fps=round(fps, 2),
                counts_by_class=dict(self._class_counts),
                last_inference_at=self._last_inference_at,
            )


# Global singleton instance
vehicle_detector = VehicleDetector()
