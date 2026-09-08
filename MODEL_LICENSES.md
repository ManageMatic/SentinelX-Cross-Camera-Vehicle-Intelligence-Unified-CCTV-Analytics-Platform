# SentinelX — Machine Learning Model Licenses

This document tracks all AI, Computer Vision, and OCR models used in SentinelX to ensure compliance with our zero-cost, open-source mandate.

| Model / Architecture | Version / Checkpoint | Code License | Weights License | Commercial Use Allowed | Official Source | Purpose in SentinelX |
|---|---|---|---|---|---|---|
| **YOLOX (Nano/Tiny/S)** | 0.3.0 | Apache-2.0 | Apache-2.0 | Yes | https://github.com/Megvii-BaseDetection/YOLOX | Real-time vehicle detection (car, motorcycle, bus, truck) |
| **ByteTrack** | 0.1.0 | MIT | MIT | Yes | https://github.com/ifzhang/ByteTrack | Multi-object tracking for vehicle tracks within single cameras |
| **PaddleOCR / PP-OCRv4** | v4 | Apache-2.0 | Apache-2.0 | Yes | https://github.com/PaddlePaddle/PaddleOCR | License plate text recognition (ANPR) & character extraction |
| **OSNet / FastReID (Lightweight)** | OSNet-x0.25 | MIT / Apache-2.0 | MIT / Apache-2.0 | Yes | https://github.com/KaiyangZhou/deep-person-reid | Vehicle visual appearance embedding for cross-camera correlation |

### Verification Protocol
1. Model weights must come from verified public open-source releases with explicit permissive licenses (Apache-2.0, MIT, BSD).
2. Models requiring non-commercial licenses (e.g. CC BY-NC 4.0) or commercial dual licenses are strictly prohibited.
3. Every downloaded or embedded weight file must have its SHA-256 checksum recorded during the corresponding AI module implementation.
