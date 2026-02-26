# Hướng Dẫn Build PhotoFit Studio thành File .exe

## Giới Thiệu

Tài liệu này hướng dẫn cách build ứng dụng PhotoFit Studio từ mã nguồn Python thành file executable (.exe) chạy trên Windows.

## Yêu Cầu Hệ Thống

- **Hệ điều hành:** Windows 10/11 (64-bit)
- **Python:** Python 3.10 hoặc cao hơn
- **RAM:** Tối thiểu 4GB (khuyến nghị 8GB+)
- **Dung lượng đĩa:** ~500MB trống

## Các Bước Build

### Bước 1: Cài Đặt Python

1. Tải Python 3.10+ từ: https://www.python.org/downloads/
2. Trong quá trình cài đặt, **QUAN TRỌNG**:
   - ✅ Tick chọn "Add Python to PATH"
   - ✅ Tick chọn "Install pip"

### Bước 2: Cài Đặt Các Thư Viện Phụ Thuộc

Mở Terminal/Command Prompt và chạy:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Bước 3: Cấu Hình Version

Chỉnh sửa file `version.txt` để thay đổi version:

```bash
# File: version.txt
1.0.0
```

### Bước 4: Chạy Build

Cách 1 - Sử dụng file batch (khuyến nghị):
```bash
build.bat
```

Cách 2 - Chạy thủ công bằng PyInstaller:
```bash
py -3 -m PyInstaller --onefile --windowed --name PhotoFitStudio_v1.0.0 main.py --clean --add-data "models;models" --add-data "templates;templates" --add-data "config.json;." --add-data "docs;docs" --collect-all=mediapipe --collect-all=rembg --collect-all=cv2 --collect-all=PIL --collect-all=numpy --collect-all=scipy --collect-all=skimage
```

### Bước 5: Kiểm Tra Kết Quả

Sau khi build hoàn tất, file `.exe` sẽ nằm trong thư mục:
```
dist\PhotoFitStudio.exe
```

## Giải Thích Các Tham Số Build

| Tham Số | Mô Tả |
|---------|--------|
| `--onefile` | Gom tất cả thành 1 file .exe duy nhất |
| `--windowed` | Chạy ứng dụng không hiện cửa sổ console |
| `--name PhotoFitStudio` | Tên file .exe đầu ra |
| `--add-data "models;models"` | Đóng gói thư mục models vào exe |
| `--add-data "templates;templates"` | Đóng gói thư mục templates vào exe |
| `--add-data "config.json;."` | Đóng gói file config vào exe |
| `--add-data "docs;docs"` | Đóng gói thư mục docs vào exe |

## Xử Lý Sự Cố

### Lỗi: "py is not recognized"

Sử dụng `python` thay vì `py`:
```bash
python -m PyInstaller ...
```

### Lỗi: Thiếu thư viện

Cài đặt thủ công:
```bash
pip install pyinstaller opencv-python Pillow mediapipe rembg[cpu] customtkinter numpy watchdog qrcode
```

### Lỗi: Build chậm

- Đảm bảo có đủ RAM
- Tạm thời tắt các ứng dụng khác
- Build lần đầu sẽ chậm nhất (cache sau đó nhanh hơn)

## Quản Lý Version

### Cấu Hình Version

File `version.txt` chứa version hiện tại của ứng dụng:

```bash
# File: version.txt
1.0.0
```

Để thay đổi version, chỉ cần sửa file này và chạy lại build.

### Quy Tắc Đặt Tên File

Sau khi build, file .exe sẽ được tạo với 2 phiên bản:

```
dist/
├── PhotoFitStudio_v1.0.0.exe    ← Version cụ thể (theo version.txt)
└── PhotoFitStudio.exe           ← Bản mới nhất (copy từ version mới nhất)
```

### Quy Tắc Ghi Đè

- **Cùng version:** Ghi đè file cũ
- **Khác version:** Tạo file mới với version mới
- `PhotoFitStudio.exe` luôn là bản mới nhất

## Chạy Ứng Dụng Sau Khi Build

1. Copy file `PhotoFitStudio.exe` từ thư mục `dist` đến vị trí mong muốn
2. Chạy file `.exe` - ứng dụng sẽ tự động giải nén và chạy

**Lưu ý:** Lần chạy đầu tiên có thể chậm hơn vì cần giải nén các file tạm.

## Thông Tin Bổ Sung

- **Dung lượng file .exe:** ~175MB (đã bao gồm Python runtime và tất cả thư viện)
- **Thời gian build:** 3-5 phút (tùy cấu hình máy)
- **Ứng dụng tương thích:** Windows 10/11 (64-bit)

## Liên Hệ Hỗ Trợ

Nếu gặp vấn đề trong quá trình build, vui lòng kiểm tra:
1. Python đã được thêm vào PATH chưa
2. Tất cả thư viện trong requirements.txt đã được cài đặt chưa
3. Có đủ dung lượng đĩa và RAM không
