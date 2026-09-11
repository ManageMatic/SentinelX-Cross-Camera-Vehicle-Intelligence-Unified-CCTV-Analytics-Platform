"""Forensic Image Enhancement & Night-Vision Colorizer Engine for Sentinel CCTV.

Provides multi-stage low-light contrast enhancement (CLAHE in LAB color space),
unsharp masking edge sharpening, noise reduction, and IR grayscale tone-mapping
to dramatically improve license plate readability and vehicle classification.
"""

from typing import Literal
import cv2
import numpy as np


class VideoFrameEnhancer:
    """Real-time forensic image enhancement pipeline for CCTV video feeds."""

    @staticmethod
    def is_grayscale_or_low_saturation(img: np.ndarray, threshold: float = 12.0) -> bool:
        """Check if frame is black-and-white / IR night vision mode."""
        if img.ndim == 2:
            return True
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mean_saturation = np.mean(hsv[:, :, 1])
        return bool(mean_saturation < threshold)

    @classmethod
    def enhance_frame(
        cls,
        frame: np.ndarray,
        mode: Literal["hdr", "night_vision", "plate_sharpen", "color_boost"] = "hdr",
    ) -> np.ndarray:
        """Apply real-time forensic enhancement to a CCTV frame."""
        if frame is None or frame.size == 0:
            return frame

        # Ensure 3 channels
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        h, w = frame.shape[:2]

        if mode == "hdr":
            # 1. LAB Color Space CLAHE (Contrast-Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)

            clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l_channel)

            merged = cv2.merge([l_enhanced, a_channel, b_channel])
            enhanced_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

            # 2. Unsharp Masking for crisp edges
            blurred = cv2.GaussianBlur(enhanced_bgr, (0, 0), 2.5)
            sharpened = cv2.addWeighted(enhanced_bgr, 1.4, blurred, -0.4, 0)
            return np.clip(sharpened, 0, 255).astype(np.uint8)

        elif mode == "night_vision":
            # Gamma correction for deep shadow recovery
            gamma = 0.65  # < 1.0 brightens shadows
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            brightened = cv2.LUT(frame, table)

            # Color contrast enhancement
            lab = cv2.cvtColor(brightened, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            enhanced = cv2.cvtColor(cv2.merge([l_clahe, a, b]), cv2.COLOR_LAB2BGR)
            return enhanced

        elif mode == "plate_sharpen":
            # Extreme high-pass filter optimized for ANPR character separation
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(6, 6))
            eq = clahe.apply(gray)
            denoised = cv2.bilateralFilter(eq, 7, 50, 50)
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharp_gray = cv2.filter2D(denoised, -1, kernel)
            return cv2.cvtColor(sharp_gray, cv2.COLOR_GRAY2BGR)

        elif mode == "color_boost":
            # Saturation and vibrance expansion
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.2, 0, 255)
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        return frame


video_frame_enhancer = VideoFrameEnhancer()
