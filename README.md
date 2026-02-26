# 📷 PhotoFit Studio

Công cụ xử lý ảnh thẻ hàng loạt với giao diện hiện đại. Phần mềm hỗ trợ workflow 2 bước: **Tiếp nhận ảnh** → **Xử lý hoàn thiện**.

---

## ✨ Tính năng

### 📥 Menu Tiếp nhận
- **Tiếp nhận ảnh**: Chọn thư mục capture, đổi tên ảnh theo MSSV
- **Resize thumbnail**: Tự động resize ảnh theo kích thước cấu hình
- **Auto-calculate**: Tính toán kích thước tự động theo tỷ lệ ảnh gốc (giống Paint)
- **Preview**: Click vào ảnh để xem trước khi xử lý
- **Tự động refresh**: Phát hiện ảnh mới trong thư mục capture

### 🔧 Menu Xử lý
- **Batch Processing**: Xử lý hàng loạt ảnh từ thư mục input
- **Face Detection**: Tự động nhận diện khuôn mặt, căn chỉnh và crop
- **Làm đẹp**: Bilateral filter + Frequency separation (3 mức: nhẹ/vừa/mạnh)
- **Auto Brightness**: Tự động cân bằng sáng/tương phản
- **Làm mịn rìa tóc**: Giảm tóc bay, làm mịn edges
- **Xóa/Thay nền**: AI-powered (rembg/U2Net), thay nền solid color
- **AI Enhance**: Tăng cường chất lượng ảnh (sharpness, colors, denoise, super resolution)
- **Resize chuẩn**: Preset ảnh thẻ VN (2x3, 3x4, 4x6, passport) + custom size
- **DPI embedding**: Embed DPI metadata (300dpi cho in ấn)
- **Preview Before/After**: So sánh trước/sau xử lý
- **Fullscreen Viewer**: Xem toàn màn hình để so sánh
- **Toggle trạng thái**: Đánh dấu ảnh đã hoàn thành/chưa hoàn thành
- **Parallel processing**: Xử lý đa luồng với progress bar

---

## 🎨 Giao diện

- **Dark Theme**: Giao diện tối hiện đại với CustomTkinter
- **2 Menu chính**: Tiếp nhận & Xử lý với sidebar cấu hình riêng
- **Cấu hình linh hoạt**: Import/Export cấu hình qua file JSON
- **Lưu tự động**: Đường dẫn thư mục được lưu vào config

---

## 🔧 Yêu cầu

- Python 3.10+
- Windows / macOS / Linux

---

## 📦 Cài đặt

```bash
cd photofit-studio

# Tạo virtual environment (khuyến nghị)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Cài đặt dependencies
pip install -r requirements.txt
```

> **Lưu ý**: Lần đầu chạy, rembg sẽ tự động tải model U2Net (~170MB).

---

## 🚀 Chạy ứng dụng

```bash
python main.py
```

---

## 📖 Hướng dẫn sử dụng

### 📥 Menu Tiếp nhận

1. Chọn thư mục **Capture** (nơi chứa ảnh chụp)
2. Danh sách ảnh hiển thị bên trái
3. Click vào ảnh để xem **preview lớn**
4. Cấu hình trong sidebar:
   - **Đường dẫn Gốc**: Thư mục lưu ảnh gốc (đổi tên = MSSV)
   - **Đường dẫn Resize**: Thư mục lưu ảnh đã resize
   - **Width/Height**: Kích thước resize
   - **Auto tính**: Bật để tự động tính theo tỷ lệ ảnh
5. Nhập **MSSV** vào ô text
6. Bấm nút **"▶ XỬ LÝ"** để tiếp nhận

📁 Ảnh sẽ được lưu vào:
- Thư mục **Gốc** - Ảnh gốc đổi tên = MSSV
- Thư mục **Resize** - Ảnh đã resize

### 🔧 Menu Xử lý

1. Chọn thư mục **Input** (chứa ảnh đã tiếp nhận)
2. Chọn thư mục **Output** (nơi lưu ảnh đã xử lý)
3. Cấu hình các tùy chọn trong sidebar:
   - **Làm đẹp (Beautify)**: Tùy chỉnh mức độ
   - **Tách nền (Background)**: Màu nền, làm mịn biên
   - **AI Enhance**: Tăng cường chất lượng ảnh
   - **Resize**: Kích thước chuẩn thẻ (3x4, 4x6,...)
4. Bấm **"▶ BẮT ĐẦU XỬ LÝ"**
5. Có thể toggle trạng thái ảnh để xử lý lại

### ⚙️ Cấu hình

- Nhấn nút **"⚙️ Cấu hình"** trên header
- **👁 Xem**: Xem cấu hình hiện tại
- **💾 Lưu**: Lưu cấu hình hiện tại vào file
- **📥 Import**: Nhập cấu hình từ file
- **📤 Export**: Xuất cấu hình ra file để chia sẻ

---

## 📐 Preset kích thước

| Preset | Kích thước | Pixel (300dpi) | Dùng cho |
|--------|-----------|----------------|----------|
| 2x3 | 2×3 cm | 236×354 | Thẻ nhỏ |
| 3x4 | 3×4 cm | 354×472 | CMND/CCCD/Bằng lái |
| 4x6 | 4×6 cm | 472×709 | Visa/Hộ chiếu |
| Passport | 3.5×4.5 cm | 413×531 | ICAO Passport |

---

## 🎨 Màu nền preset

| Tên | Mã màu | Dùng cho |
|-----|--------|----------|
| Trắng | `#FFFFFF` | Ảnh thẻ phổ thông |
| Xanh dương | `#1C86EE` | CMND/CCCD |
| Đỏ | `#DC143C` | Một số loại thẻ |
| Xanh lá | `#00A86B` | Hộ chiếu |
| Xám nhạt | `#E8E8E8` | Professional headshot |

---

## 📂 Cấu trúc project

```
photofit-studio/
├── main.py                    # Entry point
├── config.json                # Configuration file
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore
├── src/
│   ├── config_manager.py     # Config load/save
│   ├── processor.py           # Main processing pipeline
│   ├── face_detector.py      # Face detection (MediaPipe)
│   ├── beautifier.py          # Skin smoothing, brightness
│   ├── background.py         # Background removal (rembg)
│   ├── resizer.py             # Resize + DPI
│   ├── batch_runner.py        # Parallel batch processing
│   ├── ai_enhancer.py        # AI enhancement
│   └── utils.py               # Helper functions
└── ui/
    ├── main_window.py         # Main GUI window
    ├── import_panel.py        # Import panel
    ├── import_settings_panel.py  # Import settings sidebar
    ├── settings_panel.py      # Process settings sidebar
    ├── preview_panel.py       # Before/After preview
    ├── progress_panel.py      # Progress bar + log
    └── fullscreen_viewer.py   # Fullscreen comparison
```

---

## 📂 Cấu trúc thư mục làm việc

```
PhotoFit Studio/
├── capture/      ← Ảnh chụp (input ban đầu)
├── original/     ← Ảnh gốc (đổi tên = MSSV)
├── small/        ← Ảnh thumbnail (resize)
├── processed/    ← Ảnh đã xử lý (tách nền, làm đẹp)
└── final/        ← Ảnh thẻ hoàn chỉnh (output)
```

---

## 🐛 Xử lý lỗi

- **Ảnh không có mặt**: Tự động skip → copy vào `_skipped/`
- **Ảnh nhiều mặt**: Lấy mặt lớn nhất (gần camera nhất)
- **File lỗi**: Skip + ghi log, tiếp tục batch
- **Hủy giữa chừng**: Giữ nguyên ảnh đã xử lý xong

---

## 📄 License

MIT License
