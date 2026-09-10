"""ByteTrack Multi-Object Vehicle Tracking Engine (Module 11).

Associates vehicle detections across sequential CCTV video frames using Kalman Filter motion
prediction and Two-Stage Hungarian / Linear Assignment matching with duplicate OCR suppression
and persistent spatial trajectory generation.
"""

import logging
import math
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import linear_sum_assignment

from app.schemas.detection import BoundingBox, DetectedVehicle, VehicleClass
from app.schemas.tracking import (
    FrameTrackingResult,
    TrackedVehicle,
    TrackerConfig,
    TrackerTelemetry,
    TrackState,
    TrajectoryPoint,
)

logger = logging.getLogger("sentinelx.tracker")


class KalmanFilterTracker:
    """Discrete constant-velocity Kalman Filter for 2D bounding boxes."""

    def __init__(self) -> None:
        ndim, dt = 4, 1.0

        # Motion model matrix (8x8)
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt

        # Measurement projection matrix (4x8)
        self._update_mat = np.eye(ndim, 2 * ndim)

        # Noise scale weights
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create new track state vector [cx, cy, a, h, 0, 0, 0, 0]."""
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]

        std = [
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[3],
            1e-2,
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            1e-5,
            10 * self._std_weight_velocity * measurement[3],
        ]
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict state forward one time-step."""
        std_pos = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-2,
            self._std_weight_position * mean[3],
        ]
        std_vel = [
            self._std_weight_velocity * mean[3],
            self._std_weight_velocity * mean[3],
            1e-5,
            self._std_weight_velocity * mean[3],
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))

        mean = np.dot(self._motion_mat, mean)
        covariance = (
            np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        )
        return mean, covariance

    def update(
        self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Update state estimate with newly observed detection measurement."""
        std = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-1,
            self._std_weight_position * mean[3],
        ]
        measurement_cov = np.diag(np.square(std))

        projected_mean = np.dot(self._update_mat, mean)
        projected_cov = (
            np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T))
            + measurement_cov
        )

        chol_factor, lower = cho_factor(projected_cov, lower=True, check_finite=False)
        kalman_gain = cho_solve(
            (chol_factor, lower), np.dot(covariance, self._update_mat.T).T, check_finite=False
        ).T

        innovation = measurement - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot(
            (kalman_gain, projected_cov, kalman_gain.T)
        )
        return new_mean, new_covariance


def calculate_iou_matrix(atlbrs: List[np.ndarray], btlbrs: List[np.ndarray]) -> np.ndarray:
    """Calculate pairwise IoU distance matrix between tracks and detections."""
    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    if ious.size == 0:
        return ious

    for i, a in enumerate(atlbrs):
        for j, b in enumerate(btlbrs):
            x1 = max(a[0], b[0])
            y1 = max(a[1], b[1])
            x2 = min(a[2], b[2])
            y2 = min(a[3], b[3])

            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            inter = w * h

            area_a = (a[2] - a[0]) * (a[3] - a[1])
            area_b = (b[2] - b[0]) * (b[3] - b[1])
            union = area_a + area_b - inter

            ious[i, j] = (inter / union) if union > 0 else 0.0

    return 1.0 - ious  # Return cost/distance matrix (0.0 = perfect match)


class STrack:
    """Single Object Track maintaining Kalman Filter state, trajectory, and best crop metrics."""

    _count: int = 0

    def __init__(self, detection: DetectedVehicle, kalman: KalmanFilterTracker) -> None:
        STrack._count += 1
        self.track_id: str = f"TRK-{STrack._count:05d}"
        self.camera_id: str = detection.camera_id
        self.vehicle_class: VehicleClass = detection.vehicle_class
        self.state: TrackState = TrackState.NEW

        self.kalman: KalmanFilterTracker = kalman
        self.mean: Optional[np.ndarray] = None
        self.covariance: Optional[np.ndarray] = None

        self.start_frame: int = detection.frame_index
        self.last_frame: int = detection.frame_index
        self.hits: int = 1
        self.lost_frames: int = 0

        self.current_bbox: BoundingBox = detection.bbox
        self.current_confidence: float = detection.confidence
        self.best_crop_bbox: BoundingBox = detection.bbox
        self.best_crop_confidence: float = detection.confidence
        self.best_crop_frame_idx: int = detection.frame_index
        self.color_estimate: Optional[str] = detection.color_estimate
        self.ocr_processed: bool = False

        # Spatial trajectory history (center points)
        self.trajectory: deque[TrajectoryPoint] = deque(maxlen=100)
        self._record_trajectory_point(
            detection.bbox, detection.frame_index, detection.timestamp_utc
        )

        # Initialize Kalman state
        bbox_xyah = self._bbox_to_xyah(detection.bbox)
        self.mean, self.covariance = self.kalman.initiate(bbox_xyah)

    @staticmethod
    def _bbox_to_xyah(bbox: BoundingBox) -> np.ndarray:
        """Convert BoundingBox to [cx, cy, aspect_ratio, height]."""
        cx = bbox.x1 + bbox.width / 2.0
        cy = bbox.y1 + bbox.height / 2.0
        aspect = bbox.width / max(1.0, bbox.height)
        return np.array([cx, cy, aspect, bbox.height], dtype=np.float32)

    def _xyah_to_tlbr(self) -> np.ndarray:
        """Convert Kalman state [cx, cy, aspect_ratio, height] to [x1, y1, x2, y2]."""
        if self.mean is None:
            return np.array(
                [
                    self.current_bbox.x1,
                    self.current_bbox.y1,
                    self.current_bbox.x2,
                    self.current_bbox.y2,
                ]
            )
        cx, cy, aspect, h = self.mean[:4]
        w = aspect * h
        return np.array([cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0], dtype=np.float32)

    def _record_trajectory_point(self, bbox: BoundingBox, frame_idx: int, ts: datetime) -> None:
        """Record vehicle center position along observed path."""
        cx = bbox.x1 + bbox.width / 2.0
        cy = bbox.y1 + bbox.height / 2.0
        pt = TrajectoryPoint(
            x=round(cx, 2),
            y=round(cy, 2),
            norm_x=round(bbox.norm_x1 + (bbox.norm_x2 - bbox.norm_x1) / 2.0, 4),
            norm_y=round(bbox.norm_y1 + (bbox.norm_y2 - bbox.norm_y1) / 2.0, 4),
            frame_index=frame_idx,
            timestamp_utc=ts,
        )
        self.trajectory.append(pt)

    def predict(self) -> None:
        """Predict next bounding box position with Kalman filter."""
        if self.mean is not None and self.covariance is not None:
            self.mean, self.covariance = self.kalman.predict(self.mean, self.covariance)

    def update(self, detection: DetectedVehicle, frame_idx: int) -> None:
        """Update track with newly matched detection."""
        self.hits += 1
        self.lost_frames = 0
        self.state = TrackState.TRACKED
        self.last_frame = frame_idx
        self.current_bbox = detection.bbox
        self.current_confidence = detection.confidence

        if detection.color_estimate:
            self.color_estimate = detection.color_estimate

        # Select Best Crop for downstream ANPR
        # Favors higher confidence score and larger bounding box area
        current_area = detection.bbox.width * detection.bbox.height
        best_area = self.best_crop_bbox.width * self.best_crop_bbox.height
        if detection.confidence > (self.best_crop_confidence + 0.05) or (
            abs(detection.confidence - self.best_crop_confidence) <= 0.05
            and current_area > best_area
        ):
            self.best_crop_bbox = detection.bbox
            self.best_crop_confidence = detection.confidence
            self.best_crop_frame_idx = frame_idx

        # Update trajectory
        self._record_trajectory_point(detection.bbox, frame_idx, detection.timestamp_utc)

        # Kalman state update
        measurement = self._bbox_to_xyah(detection.bbox)
        if self.mean is not None and self.covariance is not None:
            self.mean, self.covariance = self.kalman.update(self.mean, self.covariance, measurement)

    def mark_lost(self) -> None:
        """Mark track as temporarily lost/occluded."""
        self.lost_frames += 1
        self.state = TrackState.LOST

    def mark_removed(self) -> None:
        """Mark track as permanently removed."""
        self.state = TrackState.REMOVED

    def calculate_heading_deg(self) -> Optional[float]:
        """Compute motion heading angle in degrees (0-360) from recent trajectory points."""
        if len(self.trajectory) < 2:
            return None
        p1 = self.trajectory[-min(5, len(self.trajectory))]
        p2 = self.trajectory[-1]
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        if math.hypot(dx, dy) < 5.0:
            return None
        angle = math.degrees(math.atan2(dy, dx)) % 360.0
        return round(angle, 1)

    def to_schema(self) -> TrackedVehicle:
        """Convert STrack to Pydantic TrackedVehicle model."""
        return TrackedVehicle(
            track_id=self.track_id,
            camera_id=self.camera_id,
            vehicle_class=self.vehicle_class,
            state=self.state,
            start_frame=self.start_frame,
            last_frame=self.last_frame,
            total_frames_tracked=self.hits,
            current_bbox=self.current_bbox,
            current_confidence=round(self.current_confidence, 4),
            best_crop_bbox=self.best_crop_bbox,
            best_crop_confidence=round(self.best_crop_confidence, 4),
            best_crop_frame_idx=self.best_crop_frame_idx,
            trajectory=list(self.trajectory),
            color_estimate=self.color_estimate,
            direction_heading_deg=self.calculate_heading_deg(),
            is_confirmed=(self.hits >= 2),
            ocr_processed=self.ocr_processed,
        )


class ByteTracker:
    """Per-camera ByteTrack multi-object tracking instance."""

    def __init__(self, config: Optional[TrackerConfig] = None) -> None:
        self.config = config or TrackerConfig()
        self.kalman = KalmanFilterTracker()
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []
        self.frame_id: int = 0

    def update(
        self,
        detections: List[DetectedVehicle],
        frame_idx: int,
        timestamp_utc: datetime,
    ) -> List[TrackedVehicle]:
        """Execute ByteTrack 2-stage association on new frame detections."""
        self.frame_id = frame_idx

        # 1. Separate detections into High and Low confidence pools
        d_high: List[DetectedVehicle] = []
        d_low: List[DetectedVehicle] = []

        for d in detections:
            if d.confidence >= self.config.track_thresh:
                d_high.append(d)
            elif d.confidence >= 0.15:
                d_low.append(d)

        # 2. Predict Kalman state for all active and lost tracks
        all_active_tracks = [
            t
            for t in self.tracked_stracks
            if t.state == TrackState.TRACKED or t.state == TrackState.NEW
        ]
        for t in all_active_tracks:
            t.predict()
        for t in self.lost_stracks:
            t.predict()

        pool_tracks = all_active_tracks + self.lost_stracks

        # 3. Stage 1 Association: Match High Confidence Detections with Tracks
        track_boxes = [t._xyah_to_tlbr() for t in pool_tracks]
        d_high_boxes = [
            np.array([d.bbox.x1, d.bbox.y1, d.bbox.x2, d.bbox.y2], dtype=np.float32) for d in d_high
        ]

        cost_matrix_1 = calculate_iou_matrix(track_boxes, d_high_boxes)
        matched_tracks_1: Set[int] = set()
        matched_dets_1: Set[int] = set()

        if cost_matrix_1.size > 0:
            row_ind, col_ind = linear_sum_assignment(cost_matrix_1)
            for r, c in zip(row_ind, col_ind):
                # Check match threshold (1.0 - IoU <= match_thresh)
                if cost_matrix_1[r, c] <= (1.0 - (1.0 - self.config.match_thresh)):
                    pool_tracks[r].update(d_high[c], frame_idx)
                    matched_tracks_1.add(r)
                    matched_dets_1.add(c)

        unmatched_tracks_1 = [
            pool_tracks[i] for i in range(len(pool_tracks)) if i not in matched_tracks_1
        ]
        unmatched_d_high = [d_high[j] for j in range(len(d_high)) if j not in matched_dets_1]

        # 4. Stage 2 Association: Match Low Confidence Detections with Remaining Tracks
        unmatched_track_boxes = [t._xyah_to_tlbr() for t in unmatched_tracks_1]
        d_low_boxes = [
            np.array([d.bbox.x1, d.bbox.y1, d.bbox.x2, d.bbox.y2], dtype=np.float32) for d in d_low
        ]

        cost_matrix_2 = calculate_iou_matrix(unmatched_track_boxes, d_low_boxes)
        matched_tracks_2: Set[int] = set()

        if cost_matrix_2.size > 0:
            row_ind2, col_ind2 = linear_sum_assignment(cost_matrix_2)
            for r, c in zip(row_ind2, col_ind2):
                if cost_matrix_2[r, c] <= (1.0 - (1.0 - self.config.match_thresh_second)):
                    unmatched_tracks_1[r].update(d_low[c], frame_idx)
                    matched_tracks_2.add(r)

        still_unmatched_tracks = [
            unmatched_tracks_1[i]
            for i in range(len(unmatched_tracks_1))
            if i not in matched_tracks_2
        ]

        # 5. Initialize New Tracks from Unmatched High-Confidence Detections
        new_tracks: List[STrack] = []
        for d in unmatched_d_high:
            if d.confidence >= self.config.high_thresh:
                new_strack = STrack(d, self.kalman)
                new_tracks.append(new_strack)

        # 6. Update Track Pools and Lifecycles
        active_list: List[STrack] = []
        lost_list: List[STrack] = []

        # Keep newly matched and new tracks
        for t in pool_tracks:
            if t in unmatched_tracks_1 and t in still_unmatched_tracks:
                t.mark_lost()
                if t.lost_frames <= self.config.max_lost_frames:
                    lost_list.append(t)
                else:
                    t.mark_removed()
                    self.removed_stracks.append(t)
            else:
                active_list.append(t)

        active_list.extend(new_tracks)

        self.tracked_stracks = active_list
        self.lost_stracks = lost_list

        # Return active tracks
        return [
            t.to_schema()
            for t in self.tracked_stracks
            if t.state in (TrackState.TRACKED, TrackState.NEW)
        ]


class CameraTrackerManager:
    """Platform-wide coordinator managing ByteTrack instances across dynamic CCTV streams."""

    def __init__(self) -> None:
        self._trackers: Dict[str, ByteTracker] = {}
        self._lock = threading.Lock()

        # Telemetry
        self._total_tracks: int = 0
        self._latency_samples: deque[float] = deque(maxlen=100)
        self._last_tracked_at: Optional[datetime] = None

    def get_or_create_tracker(
        self, camera_id: str, config: Optional[TrackerConfig] = None
    ) -> ByteTracker:
        """Get existing tracker or initialize a new ByteTracker for camera."""
        with self._lock:
            if camera_id not in self._trackers:
                self._trackers[camera_id] = ByteTracker(config)
            return self._trackers[camera_id]

    def track_camera_frame(
        self,
        camera_id: str,
        frame_idx: int,
        detections: List[DetectedVehicle],
        timestamp_utc: Optional[datetime] = None,
    ) -> FrameTrackingResult:
        """Update multi-object tracks for a camera frame."""
        start_t = time.perf_counter()
        now_utc = timestamp_utc or datetime.now(timezone.utc)

        tracker = self.get_or_create_tracker(camera_id)
        with self._lock:
            tracked_vehicles = tracker.update(detections, frame_idx, now_utc)
            self._total_tracks += len([v for v in tracked_vehicles if v.total_frames_tracked == 1])

        latency_ms = (time.perf_counter() - start_t) * 1000.0
        with self._lock:
            self._latency_samples.append(latency_ms)
            self._last_tracked_at = now_utc

        return FrameTrackingResult(
            camera_id=camera_id,
            frame_index=frame_idx,
            timestamp_utc=now_utc,
            active_tracks_count=len(tracked_vehicles),
            tracking_latency_ms=round(latency_ms, 2),
            tracks=tracked_vehicles,
        )

    def get_active_tracks(self, camera_id: str) -> List[TrackedVehicle]:
        """Retrieve all currently active tracks on a camera feed."""
        with self._lock:
            tracker = self._trackers.get(camera_id)
        if not tracker:
            return []
        return [
            t.to_schema()
            for t in tracker.tracked_stracks
            if t.state in (TrackState.TRACKED, TrackState.NEW)
        ]

    def get_track_trajectory(
        self, camera_id: str, track_id: str
    ) -> Optional[List[TrajectoryPoint]]:
        """Retrieve spatial breadcrumbs and trajectory history for a specific track ID."""
        with self._lock:
            tracker = self._trackers.get(camera_id)
        if not tracker:
            return None

        for t in tracker.tracked_stracks + tracker.lost_stracks + tracker.removed_stracks:
            if t.track_id == track_id:
                return list(t.trajectory)
        return None

    def reset_camera(self, camera_id: str) -> bool:
        """Clear all active and lost tracks for a camera."""
        with self._lock:
            if camera_id in self._trackers:
                del self._trackers[camera_id]
                return True
        return False

    def get_telemetry(self) -> TrackerTelemetry:
        """Aggregate MOT telemetry across all cameras."""
        with self._lock:
            active_counts = {
                cam_id: len(
                    [
                        t
                        for t in trk.tracked_stracks
                        if t.state in (TrackState.TRACKED, TrackState.NEW)
                    ]
                )
                for cam_id, trk in self._trackers.items()
            }
            total_active = sum(active_counts.values())
            total_lost = sum(len(trk.lost_stracks) for trk in self._trackers.values())
            total_removed = sum(len(trk.removed_stracks) for trk in self._trackers.values())
            avg_latency = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            return TrackerTelemetry(
                total_tracks_created=self._total_tracks,
                active_tracks_count=total_active,
                lost_tracks_count=total_lost,
                removed_tracks_count=total_removed,
                average_tracking_latency_ms=round(avg_latency, 2),
                camera_active_counts=active_counts,
                last_tracked_at=self._last_tracked_at,
            )


# Global singleton instance
camera_tracker_manager = CameraTrackerManager()
