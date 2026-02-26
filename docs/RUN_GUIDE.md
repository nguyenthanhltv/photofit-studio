# Hướng dẫn Chạy, Build và Publish PhotoFit Studio v1.4

## 📋 Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Chạy ứng dụng](#2-chạy-ứng-dụng)
3. [Build thành file .exe](#3-build-thành-file-exe)
4. [Publish và chia sẻ](#4-publish-và-chia-sẻ)
5. [Câu hỏi thường gặp](#5-câu-hỏi-thường-gặp)

---

## 1. Yêu cầu hệ thống

### Tối thiểu:
- **CPU:** Intel Core i3 / AMD Ryzen 3
- **RAM:** 4 GB
- **Dung lượng đĩa:** 2 GB trống
- **Hệ điều hành:** Windows 10/11 (64-bit)

### Khuyến nghị:
- **CPU:** Intel Core i5 / AMD Ryzen 5
- **RAM:** 8 GB
- **Dung lượng đĩa:** 5 GB (cho model AI)

### Phần mềm cần thiết:
- Python 3.10+ ([Tải tại đây](https://www.python.org/downloads/))
- pip (có sẵn khi cài Python)

---

## 2. Chạy ứng dụng

### Cách 1: Chạy bằng file .bat (Khuyến nghị)

```
1. Mở thư mục: d:\ProjectEiu\Tool\photofit-studio
2. Double-click vào file: run.bat
3. Đợi cài đặt dependencies lần đầu (nếu chưa có)
4. Ứng dụng sẽ tự động khởi động
```

### Cách 2: Chạy bằng Python trực tiếp

```bash
# Mở Terminal/Command Prompt
cd d:\ProjectEiu\Tool\photofit-studio

# Cài đặt dependencies (nếu chưa có)
py -m pip install -r requirements.txt

# Chạy ứng dụng
py main.py
```

### Cách 3: Chạy bằng Python với virtual environment

```bash
# Tạo virtual environment
cd d:\ProjectEiu\Tool\photofit-studio
python -m venv venv

# Kích hoạt virtual environment
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

---

## 3. Build thành file .exe

### Cài đặt công cụ build

```bash
# Cài đặt PyInstaller
py -m pip install pyinstaller

# Hoặc cài version cụ thể
py -m pip install pyinstaller==6.3.0
```

### Bước 2: Cấu hình Version

Chỉnh sửa file `version.txt` để thay đổi version:

```bash
# File: version.txt
1.0.0
```

### Bước 3: Chạy Build

**Cách 1 - Sử dụng build.bat (Khuyến nghị):**
```bash
build.bat
```

**Cách 2 - Chạy thủ công bằng PyInstaller:**
```bash
py -3 -m PyInstaller --onefile --windowed --name "PhotoFitStudio_v1.0.0" main.py --add-data "models;models" --add-data "templates;templates" --add-data "config.json;." --add-data "docs;docs" --collect-all=mediapipe --collect-all=rembg --collect-all=cv2 --collect-all=PIL --collect-all=numpy
```

### Kết quả sau build

```
dist/
├── PhotoFitStudio_v1.0.0.exe    ← Version cụ thể (theo version.txt)
└── PhotoFitStudio.exe           ← Bản mới nhất (copy từ version mới nhất)
```

### Bước 4: Tạo file spec (cấu hình build) - Tùy chọn

Tạo file `photofit.spec` trong thư mục gốc (nếu cần tùy chỉnh nâng cao):

```python
# photofit.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/*.tflite', 'models'),
    ],
    hiddenimports=[
        'cv2', 'numpy', 'PIL', 'customtkinter', 'mediapipe', 'rembg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoFitStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoFitStudio',
)
```

### Bước 3: Chạy build

```bash
# Build thành thư mục (debug)
pyinstaller photofit.spec --clean

# Build thành một file duy nhất
pyinstaller --onefile --windowed main.py --name PhotoFitStudio
```

### Bước 4: Kiểm tra kết quả

```
Thư mục output: dist\PhotoFitStudio\
├── PhotoFitStudio.exe    ← File chạy chính
└── models/               ← Models (nếu có)
```

### Build nhanh (đơn giản nhất):

```bash
pyinstaller --onefile --windowed --name PhotoFitStudio main.py
```

---

## 4. Publish và chia sẻ

### Cách 1: Chia sẻ file .exe trực tiếp

1. Sau khi build, vào thư mục `dist\PhotoFitStudio\`
2. Nén toàn bộ thư mục thành file .zip
3. Chia sẻ file zip qua:
   - Google Drive / OneDrive / Dropbox
   - Email
   - USB/HDD

### Cách 2: Tạo Installer (nâng cao)

Sử dụng NSIS hoặc Inno Setup:

**Inno Setup Script (install.iss):**
```iss
[Setup]
AppName=PhotoFit Studio
AppVersion=1.4
DefaultDirName={autopf}\PhotoFit Studio
DefaultGroupName=PhotoFit Studio
OutputBaseFilename=PhotoFitStudio-Setup-v1.4
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\PhotoFitStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Run]
Filename: "{app}\PhotoFitStudio.exe"; Description: "Launch PhotoFit Studio"; Flags: postinstall nowait
```

### Cách 3: Upload lên GitHub Releases

```bash
# 1. Tạo tag mới
git tag v1.4

# 2. Push tag
git push origin v1.4

# 3. Tạo Release trên GitHub
# - Vào https://github.com/nguyenthanhltv/photofit-studio/releases
# - Tạo New Release
# - Upload file .exe/.zip
```

### Cách 4: Tạo Portable Version

```batch
@echo off
REM Tạo portable version
mkdir "PhotoFitStudio-Portable-v1.4"
xcopy /E /I /Y "dist\PhotoFitStudio" "PhotoFitStudio-Portable-v1.4"
copy "config.json" "PhotoFitStudio-Portable-v1.4\"
pause
```

---

## 5. Câu hỏi thường gặp

### Q1: Lỗi "Python not found"
**A:** Cài Python từ https://www.python.org/ và chọn "Add Python to PATH"

### Q2: Lỗi "Module not found"
**A:** Chạy lệnh:
```bash
py -m pip install -r requirements.txt
```

### Q3: Ứng dụng chạy chậm
**A:**
- Tắt AI Enhancement nếu không cần
- Giảm số lượng ảnh xử lý cùng lúc
- Tắt các ứng dụng khác đang chạy

### Q4: Lỗi khi build .exe
**A:**
```bash
# Cập nhật pip
py -m pip install --upgrade pip

# Cập nhật PyInstaller
py -m pip install --upgrade pyinstaller

# Xóa cache và build lại
rmdir /S /Q build dist __pycache__
pyinstaller --onefile --windowed main.py
```

### Q5: File .exe bị Antivirus chặn
**A:** Đây là hiện tượng bình thường với PyInstaller. Bạn có thể:
- Add exception trong Antivirus
- Sign code (nếu có certificate)
- Upload lên VirusTotal để verify

### Q6: Làm sao update lên version mới?
```bash
# Pull code mới
git pull origin main

# Cập nhật dependencies
py -m pip install -r requirements.txt

# Build lại
pyinstaller --onefile --windowed main.py
```

---

## 📞 Hỗ trợ

Nếu gặp vấn đề khác, vui lòng:
1. Xem log trong `logs/processor.log`
2. Kiểm tra Python version: `python --version`
3. Liên hệ qua GitHub Issues

---

**Phiên bản:** 1.4
**Ngày cập nhật:** 2026-02-25
**Tác giả:** PhotoFit Studio Team
