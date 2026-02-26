# Tài liệu Kỹ thuật - AI Enhancement Module

## 1. Tổng quan

Module AI Enhancement (`src/ai_enhancer.py`) được phát triển để nâng cao chất lượng ảnh đầu ra của PhotoFit Studio. Module này sử dụng các thuật toán xử lý ảnh nâng cao của OpenCV kết hợp với các kỹ thuật AI-based processing.

### Vấn đề giải quyết

Module Beautifier gốc chỉ sử dụng:
- Bilateral Filter (làm mịn da)
- CLAHE (cải thiện tương phản)
- Các thuật toán truyền thống không có khả năng "thông minh"

AI Enhancement bổ sung:
- Smart Denoising với nhận diện vùng da
- Color Enhancement với bảo vệ tông da
- Multi-scale Sharpening
- Edge-preserving Super Resolution

---

## 2. Kiến trúc Module

### 2.1 Class: AIEnhancer

```python
from src.ai_enhancer import AIEnhancer

# Khởi tạo
enhancer = AIEnhancer(level="medium")  # light, medium, strong

# Xử lý ảnh
result = enhancer.process(
    image,                      # Ảnh input (numpy array BGR)
    enhance_sharpness=True,    # Tăng độ nét
    enhance_colors=True,        # Cải thiện màu sắc
    denoise=True,               # Khử nhiễu
    super_resolve=False,        # Super Resolution
    scale=2                     # Tỷ lệ phóng (khi super_resolve=True)
)
```

### 2.2 Cấu hình Level

| Level | sharpen_strength | denoise_strength | contrast_boost | saturation_boost |
|-------|------------------|------------------|----------------|------------------|
| Light | 0.3 | 0.2 | 1.05 | 1.1 |
| Medium | 0.5 | 0.4 | 1.1 | 1.15 |
| Strong | 0.7 | 0.6 | 1.15 | 1.2 |

---

## 3. Chi tiết từng thành phần

### 3.1 Smart Denoising (`smart_denoise`)

**Mục đích:** Khử nhiễu ảnh mà không làm mất chi tiết da mặt

**Thuật toán:**
1. Tạo mask vùng da sử dụng 2 không gian màu:
   - YCrCb (skin color range)
   - HSV (skin hue range)
2. Xử lý riêng biệt:
   - Vùng KHÔNG phải da: fastNlMeansDenoisingColored (mạnh)
   - Vùng da: Bilateral Filter (nhẹ, bảo toàn texture)
3. Kết hợp 2 vùng

**Code:**
```python
def smart_denoise(self, image: np.ndarray) -> np.ndarray:
    skin_mask = self._create_skin_mask(image)
    
    # Apply strong denoising on non-skin areas
    non_skin = cv2.bitwise_and(image, image, mask=255 - skin_mask)
    denoised_bg = cv2.fastNlMeansDenoisingColored(non_skin, ...)
    
    # Gentle denoise for skin areas
    skin = cv2.bitwise_and(image, image, mask=skin_mask)
    denoised_skin = cv2.bilateralFilter(skin, d=7, sigmaColor=..., sigmaSpace=...)
    
    result = cv2.add(denoised_bg, denoised_skin)
```

### 3.2 Enhance Colors (`enhance_colors`)

**Mục đích:** Cải thiện màu sắc tự nhiên, giữ tông da

**Thuật toán:**
1. **CLAHE trên L channel (LAB):**
   - Tăng cường local contrast
   - Thích ứng với điều kiện ánh sáng khác nhau
2. **Saturation Boost có bảo vệ da:**
   - Tăng saturation cho vùng không phải da
   - Giữ nguyên saturation vùng da
3. **Warm tone adjustment:**
   - Thêm warmth nhẹ cho vùng da ( healthier look)

**Code:**
```python
def enhance_colors(self, image: np.ndarray) -> np.ndarray:
    # CLAHE on L channel
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    # Skin-protected saturation boost
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    s_boosted = np.where(skin_mask > 127, s, s * saturation_boost)
    
    # Warmth adjustment for skin
    result[skin_bool, 2] += warmth_amount  # Add red/yellow
```

### 3.3 Optimize Sharpness (`optimize_sharpness`)

**Mục đích:** Tăng độ nét ảnh mà không tạo artifact

**Thuật toán:**
1. **Multi-scale Unsharp Masking:**
   - Scale 1: Gaussian blur σ=1.0 → nhẹ
   - Scale 2: Gaussian blur σ=2.0 → vừa
   - Scale 3: Gaussian blur σ=4.0 → mạnh
2. **Laplacian Edge Enhancement:**
   - Phát hiện cạnh bằng Laplacian
   - Cộng gộp edge vào ảnh gốc

**Code:**
```python
def _enhance_details(self, image, strength):
    # Multi-scale unsharp mask
    blur1 = cv2.GaussianBlur(image, (0, 0), 1.0)
    sharp1 = cv2.addWeighted(image, 1 + strength*0.3, blur1, -strength*0.3, 0)
    
    blur2 = cv2.GaussianBlur(image, (0, 0), 2.0)
    sharp2 = cv2.addWeighted(image, 1 + strength*0.4, blur2, -strength*0.4, 0)
    
    # Blend all scales
    result = cv2.addWeighted(sharp1, 0.4, sharp2, 0.6, 0)
    
    # Add Laplacian edges
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    result = cv2.addWeighted(result, 1, edge_layer, strength*0.3, 0)
```

### 3.4 Super Resolution (`super_resolution`)

**Mục đích:** Phóng to ảnh không bị vỡ pixel

**Thuật toán:**
1. **INTER_LANCZOS4** - Chất lượng cao nhất trong OpenCV
2. **Detail Enhancement** - Áp dụng sharpening sau khi resize

**Code:**
```python
def super_resolution(self, image, scale=2):
    # High-quality upscale
    result = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Edge-preserving refinement
    result = self._enhance_details(result, strength=0.3)
    
    return result
```

---

## 4. Tích hợp vào Pipeline

### 4.1 Pipeline cũ

```
Input → Beautify → Background → Face Detection → Resize → Output
```

### 4.2 Pipeline mới (v1.4)

```
Input → Beautify → Background → AI Enhancement → Face Detection → Resize → Output
```

### 4.3 Cấu hình trong processor.py

```python
# Trong process_image()
ai_cfg = self.config.get("ai_enhance", {})

if ai_cfg.get("enabled", True):
    result = self.ai_enhancer.process(
        result,
        enhance_sharpness=ai_cfg.get("enhance_sharpness", True),
        enhance_colors=ai_cfg.get("enhance_colors", True),
        denoise=ai_cfg.get("denoise", True),
        super_resolve=ai_cfg.get("super_resolution", False),
        scale=ai_cfg.get("scale", 2)
    )
```

---

## 5. Cấu hình hệ thống

### 5.1 Config JSON

```json
{
  "ai_enhance": {
    "enabled": true,
    "level": "medium",
    "enhance_sharpness": true,
    "enhance_colors": true,
    "denoise": true,
    "super_resolution": false,
    "scale": 2
  }
}
```

### 5.2 Ý nghĩa các tham số

| Tham số | Kiểu | Mặc định | Mô tả |
|---------|------|----------|-------|
| enabled | bool | true | Bật/tắt AI Enhancement |
| level | string | medium | Mức độ xử lý (light/medium/strong) |
| enhance_sharpness | bool | true | Tăng độ nét |
| enhance_colors | bool | true | Cải thiện màu sắc |
| denoise | bool | true | Khử nhiễu |
| super_resolution | bool | false | Phóng to nét |
| scale | int | 2 | Tỷ lệ phóng (2, 4) |

---

## 6. Giao diện người dùng

### 6.1 Vị trí trong Settings Panel

```
Settings Panel
├── ✨ Làm đẹp
├── 🎨 Nền ảnh
├── 🤖 AI Nâng cao          ← THÊM MỚI
│   ├── Bật AI nâng cao chất lượng
│   ├── Mức độ AI [Nhẹ|Vừa|Mạnh]
│   ├── Tăng độ nét (Sharpness)
│   ├── Cải thiện màu sắc (Colors)
│   ├── Khử nhiễu (Denoise)
│   └── Super Resolution (Phóng to nét)
├── 📐 Kích thước
├── 💾 Output
└── ⚙️ Xử lý
```

---

## 7. Hiệu năng

### 7.1 Thời gian xử lý ước tính

Với ảnh 3x4 cm @ 300 DPI (354x472 pixels):

| Tính năng | Thời gian thêm |
|-----------|-----------------|
| Sharpness | ~50ms |
| Colors | ~80ms |
| Denoise | ~200ms |
| Super Resolution (2x) | ~150ms |
| **Tổng (all enabled)** | **~500ms** |

### 7.2 Yêu cầu hệ thống

- **CPU:** Intel Core i3 hoặc tương đương
- **RAM:** 4GB trở lên
- **Không yêu cầu GPU** (chạy trên CPU)
- **OpenCV:** 4.8.0+

---

## 8. So sánh trước/sau

### Trước khi dùng AI Enhancement:
- Ảnh có thể bị mờ, vỡ pixel khi resize
- Màu sắc nhợt nhạt, thiếu contrast
- Nhiễu trong điều kiện ánh sáng yếu
- Da mặt có thể bị làm mịn quá mức

### Sau khi dùng AI Enhancement:
- ✅ Độ nét tốt hơn, chi tiết rõ ràng
- ✅ Màu sắc tự nhiên, ấm áp
- ✅ Nhiễu được giảm thiểu
- ✅ Texture da được bảo toàn

---

## 9. Xử lý sự cố

### 9.1 Lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|------------|
| Module import error | Thiếu opencv-python | `pip install opencv-python` |
| Ảnh bị quá mịn | Level đặt quá cao | Chuyển sang "Nhẹ" |
| Màu sắc không tự nhiên | Tắt enhance_colors | Bật enhance_colors |
| Xử lý quá chậm | Bật nhiều tính năng | Tắt super_resolution |

### 9.2 Debug logging

```python
# Bật debug để xem chi tiết
import logging
logging.getLogger("ai_enhancer").setLevel(logging.DEBUG)
```

---

## 10. Phát triển tiếp theo

### 10.1 Cải tiến có thể thêm

1. **Real-ESRGAN Integration:**
   - Thay thế Super Resolution bằng AI model thực sự
   - Cần GPU hoặc model nhẹ hơn

2. **Face Restoration:**
   - GFPGAN/CodeFormer cho khuôn mặt bị mờ nặng

3. **AI Color Grading:**
   - Tự động điều chỉnh color tone theo loại ảnh thẻ

### 10.2 Tối ưu hiệu năng

- Chạy trên GPU với OpenCV DNN
- Multi-threading cho batch processing
- Cache kết quả trung gian

---

## 11. Tham khảo

- OpenCV Documentation: https://docs.opencv.org/
- CLAHE: https://en.wikipedia.org/wiki/Adaptive_histogram_equalization
- Bilateral Filter: https://people.csail.mit.edu/sparis/bf/
- Non-local Means Denoising: https://www.ipol.im/pub/art/2011/l_bm/

---

**Phiên bản:** 1.4  
**Ngày cập nhật:** 2026-02-25  
**Tác giả:** PhotoFit Studio Team
