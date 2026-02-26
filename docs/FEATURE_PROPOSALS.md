# Feature Proposals for PhotoFit Studio

> Document lưu trữ các đề xuất tính năng nâng cao cho dự án PhotoFit Studio.

---

## 📋 Mục lục

1. [Tổng quan](#tổng-quan)
2. [Option A: AI Features](#option-a-ai-features)
3. [Option B: Workflow & Automation](#option-b-workflow--automation)
4. [Option C: Collaboration & Export](#option-c-collaboration--export)
5. [Option D: Quality Assurance](#option-d-quality-assurance)
6. [Option E: Performance & Infrastructure](#option-e-performance--infrastructure)
7. [Kế hoạch triển khai](#kế-hoạch-triển-khai)

---

## Tổng quan

PhotoFit Studio hiện tại có các tính năng:
- Face Detection & Alignment (MediaPipe)
- Background Removal (rembg/U2Net)
- Beautification (Bilateral Filter, CLAHE)
- AI Enhancement (sharpen, colors, denoise, super resolution)
- Batch Processing với parallel processing
- Resize với presets (2x3, 3x4, 4x6, passport)
- Preview Before/After & Fullscreen Viewer
- Import/Export cấu hình JSON

---

## Option A: AI Features

### 🎭 Face Restoration (GFPGAN/CodeFormer)
- **Mô tả**: Khôi phục khuôn mặt bị mờ nặng
- **Dependencies**: `opencv-python`, `torch`, `timm`, `facenet-pytorch`
- **Effort**: HIGH

### 🔍 Super Resolution (Real-ESRGAN)
- **Mô tả**: Thay thế INTER_LANCZOS4 bằng AI model
- **Dependencies**: `opencv-python`, `torch`, ` realesrgan-ncnn-vulkan-python`
- **Effort**: HIGH

### 😊 Face Expression Correction
- **Mô tả**: Tự động phát hiện và sửa mắt nhắm/miệng hở
- **Dependencies**: `mediapipe`, custom logic
- **Effort**: MEDIUM

### 👁 Eye Enhancement
- **Mô tả**: Tăng độ sáng mắt, làm rõ mống mắt
- **Dependencies**: `mediapipe`, `opencv-python`
- **Effort**: LOW

### 🦷 Teeth Whitening
- **Mô tả**: Tự động phát hiện và làm trắng răng
- **Dependencies**: `mediapipe`, `opencv-python`
- **Effort**: LOW

---

## Option B: Workflow & Automation

### 📋 Template System ✅ (Ưu tiên cao)
- **Mô tả**: Lưu và quản lý các preset xử lý, quick-apply template cho từng loại thẻ
- **Dependencies**: `json`, `os`
- **Effort**: LOW
- **Trạng thái**: Chưa bắt đầu
- **Files cần tạo/sửa**:
  - `src/template_manager.py` (new)
  - `ui/template_panel.py` (new)
  - Update `config_manager.py`

### 🔄 Auto-Run Mode ✅ (Ưu tiên cao)
- **Mô tả**: Watch folder - tự động xử lý khi có ảnh mới
- **Dependencies**: `watchdog`
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu
- **Files cần tạo/sửa**:
  - `src/file_watcher.py` (new)
  - Update `batch_runner.py`

### 📊 Statistics Dashboard ✅ (Ưu tiên trung bình)
- **Mô tả**: Thống kê số ảnh đã xử lý, thời gian xử lý trung bình, error rate
- **Dependencies**: `json`, `sqlite` (optional)
- **Effort**: LOW
- **Trạng thái**: Chưa bắt đầu
- **Files cần tạo/sửa**:
  - `src/statistics.py` (new)
  - `ui/stats_panel.py` (new)

### 🎯 Smart Auto-Detection
- **Mô tả**: Tự động phát hiện loại ảnh thẻ cần làm
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu

### 📤 Batch Export ✅ (Ưu tiên trung bình)
- **Mô tả**: Export nhiều định dạng cùng lúc (jpg, png, pdf)
- **Dependencies**: `Pillow`
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu

### 💾 Project Files
- **Mô tả**: Lưu trạng thái project để tiếp tục sau
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu

---

## Option C: Collaboration & Export

### 🖨 Print Layout ✅ (Ưu tiên trung bình)
- **Mô tả**: Tạo layout in ấn (4x6, 2x3 trên A4)
- **Dependencies**: `Pillow`
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu
- **Files cần tạo/sửa**:
  - `src/print_layout.py` (new)
  - `ui/print_panel.py` (new)

### 📧 Direct Share
- **Mô tả**: Export trực tiếp qua email, tích hợp cloud
- **Dependencies**: `google-api-python-client` (optional)
- **Effort**: HIGH
- **Trạng thái**: Chưa bắt đầu

### 🔗 QR Code Generation
- **Mô tả**: Tạo QR chứa thông tin sinh viên
- **Dependencies**: `qrcode`
- **Effort**: LOW
- **Trạng thái**: Chưa bắt đầu

### 📱 Mobile App Integration
- **Mô tả**: Web server nhúng để xem ảnh từ điện thoại
- **Dependencies**: `flask` hoặc `http.server`
- **Effort**: HIGH
- **Trạng thái**: Chưa bắt đầu

---

## Option D: Quality Assurance

### ✅ Auto Quality Check
- **Mô tả**: Kiểm tra ảnh có khuôn mặt rõ không, cảnh báo ảnh không đạt
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu

### 👤 Face Quality Scoring
- **Mô tả**: Đánh giá độ rõ nét khuôn mặt (0-100)
- **Effort**: MEDIUM
- **Trạng thái**: Chưa bắt đầu

### 🎯 Compliance Check
- **Mô tả**: Kiểm tra ảnh có đúng tiêu chuẩn không
- **Effort**: HIGH
- **Trạng thái**: Chưa bắt đầu

---

## Option E: Performance & Infrastructure

### 🚀 GPU Acceleration
- **Mô tả**: Sử dụng CUDA cho OpenCV
- **Dependencies**: `opencv-python`, `cupy` (optional)
- **Effort**: HIGH

### 💾 Caching System
- **Mô tả**: Cache kết quả trung gian
- **Effort**: MEDIUM

### 🌐 Web Interface
- **Mô tả**: Giao diện web thay thế cho desktop
- **Dependencies**: `flask`, `react` hoặc `htmx`
- **Effort**: HIGH

---

## Kế hoạch triển khai

### Phase 1: Dễ triển khai (Low Effort)
- [x] Template System - `src/template_manager.py`, `ui/template_panel.py`
- [x] QR Code Generation - `src/qr_generator.py`
- [x] Eye Enhancement - `src/beautifier.py` (enhance_eyes method)
- [x] Teeth Whitening - `src/beautifier.py` (whiten_teeth method)

### Phase 2: Trung bình (Medium Effort)
- [x] Auto-Run Mode - `src/file_watcher.py`
- [x] Statistics Dashboard - `src/statistics.py`
- [x] Print Layout - `src/print_layout.py`
- [x] Batch Export - `src/batch_exporter.py`

### Phase 3: Khó (High Effort)
- [x] Face Restoration - `src/face_restorer.py` (with traditional fallback)
- [x] Super Resolution - `src/face_restorer.py` (Lanczos + sharpening fallback)
- [x] Web Interface - `src/web_server.py` (embedded HTTP server)
- [x] GPU Acceleration - `src/gpu_accelerator.py` (detection & optimization)

---

## Đánh giá ưu tiên

| Priority | Tính năng | Effort | Giá trị |
|----------|-----------|--------|---------|
| 🔴 Cao | Template System | Low | High |
| 🔴 Cao | Auto-Run Mode | Medium | High |
| 🟡 Trung | Statistics Dashboard | Low | Medium |
| 🟡 Trung | Print Layout | Medium | High |
| 🟡 Trung | Batch Export | Medium | Medium |
| 🟢 Thấp | QR Code | Low | Low |

---

*Document created: 2026-02-26*
*Last updated: 2026-02-26*
