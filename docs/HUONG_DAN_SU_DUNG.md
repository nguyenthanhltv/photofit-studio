# Hướng Dẫn Sử Dụng Chi Tiết - PhotoFit Studio

## 1) Tổng quan

PhotoFit Studio là công cụ xử lý ảnh thẻ hàng loạt, gồm các bước:

1. Làm đẹp ảnh (mịn da, cân sáng, làm mịn tóc)
2. Xóa/thay nền
3. Tự canh chủ thể (người) vào khung theo kích thước ảnh đích
4. Resize theo preset ảnh thẻ
5. Xuất file kèm DPI để in

---

## 2) Giao diện chính

### Thanh trên cùng

- **Save Config**: Lưu toàn bộ cài đặt hiện tại vào `config.json`.
- **Thông tin**: Xem thông tin phần mềm và phiên bản hiện tại.
- **Update logs**: Xem lịch sử thay đổi phiên bản.
- **Hướng dẫn**: Mở tài liệu hướng dẫn này.

> Từ phiên bản mới, phần mềm đã đổi tên thành **PhotoFit Studio**.

### Danh sách ảnh (Images)

- Mỗi ảnh hiển thị:
  - **Thumbnail nhỏ** (ảnh thu nhỏ)
  - **Tên file**
  - **Trạng thái**: Chờ xử lý / Hoàn tất / Lỗi
- Khi bấm vào 1 ảnh trong danh sách, panel Preview sẽ hiển thị đúng ảnh đó.
- Trong lúc batch đang chạy, ảnh đang xử lý sẽ tự động được chọn và cập nhật trạng thái.

### Preview BEFORE / AFTER

- **BEFORE**: ảnh gốc tương ứng với item đang chọn/đang xử lý.
- **AFTER**: ảnh kết quả sau xử lý.
- Khi chạy nhiều ảnh, preview sẽ **tự đổi theo từng ảnh** để dễ kiểm tra realtime.

### Khu vực trái (Settings)

#### A. Làm đẹp
- **Bật làm đẹp**: Bật/tắt toàn bộ xử lý làm đẹp.
- **Mức độ**:
  - `Nhẹ` (`light`): giữ tự nhiên, chỉnh ít.
  - `Vừa` (`medium`): cân bằng.
  - `Mạnh` (`strong`): xử lý rõ hơn.
- **Làm mịn da**: giảm hạt, mịn vùng da.
- **Auto sáng / tương phản**: cân lại ánh sáng toàn ảnh.
- **Làm mịn rìa tóc**: giảm răng cưa/tóc bay ở biên.

#### B. Nền ảnh
- **Xóa / Thay nền**: dùng AI tách chủ thể khỏi nền cũ.
- **Màu nền**: chọn preset nhanh (trắng/xanh/đỏ/...).
- **Custom Hex**: nhập mã màu thủ công, ví dụ `#FFFFFF`.
- **Làm mịn viền**: làm mềm ranh giới giữa người và nền mới.

#### C. Kích thước
- **Resize ảnh**: bật/tắt đổi kích thước đầu ra.
- **Tự canh chủ thể vào khung**:
  - Khi bật: hệ thống tự phát hiện mặt và canh bố cục ảnh thẻ.
  - Khi tắt: chỉ resize cơ bản theo kích thước.
- **Khoảng cách** (đã rút gọn để dễ nhìn):
  - `Gần` (`near`): chủ thể lớn hơn trong khung.
  - `Vừa` (`medium`): bố cục cân bằng (khuyến nghị mặc định).
  - `Xa` (`far`): chừa khoảng trống nhiều hơn quanh chủ thể.
- Thuật toán mới ưu tiên **giữ bố cục ảnh gốc hợp lý** theo tỷ lệ ảnh đích, hạn chế cắt mất nhân vật.
- **Preset**: chọn kích thước chuẩn (2x3, 3x4, 4x6, passport, custom).
- **W × H**: nhập kích thước pixel thủ công khi cần.
- **DPI**: chọn 72 / 150 / 300 (in ảnh thẻ nên dùng 300 DPI).

#### D. Output
- **Format**: JPG hoặc PNG.
- **Quality**: chất lượng nén (ảnh càng đẹp thì dung lượng càng lớn).
- **Ghi đè file trùng tên**: cho phép thay thế file cũ cùng tên.

#### E. Xử lý
- **Workers**: số luồng xử lý song song.
- **Bỏ qua ảnh lỗi, tiếp tục**: lỗi từng ảnh sẽ không dừng toàn bộ batch.

---

## 3) Quy trình xử lý chuẩn

1. **Chọn Input**: bấm `Browse` ở ô Input để chọn thư mục ảnh gốc.
2. **Chọn Output**: bấm `Browse` ở ô Output để chọn thư mục xuất.
3. **Thiết lập thông số** ở panel trái.
4. **Bấm Start Processing** để bắt đầu.
5. Theo dõi:
   - Danh sách file,
   - progress bar,
   - preview trước/sau,
   - log trạng thái.
6. Có thể bấm **Stop** để dừng giữa chừng.

---

## 4) Gợi ý cài đặt nhanh theo nhu cầu

### Ảnh thẻ phổ thông 3x4
- Preset: `3x4`
- Tự canh chủ thể: Bật
- Khoảng cách: `Vừa`
- Nền: Trắng `#FFFFFF`
- DPI: `300`

### Muốn mặt lớn hơn
- Giữ preset theo nhu cầu
- Đổi **Khoảng cách** sang `Gần`

### Muốn thấy nhiều vai/ngực hơn
- Đổi **Khoảng cách** sang `Xa`

### Khi đổi nhiều kích thước (3x4, 4x6, passport) nhưng vẫn muốn bố cục tự nhiên
- Bật **Tự canh chủ thể vào khung**
- Để **Khoảng cách = Vừa** trước
- Nếu mặt quá to, đổi sang **Xa**
- Nếu mặt quá nhỏ, đổi sang **Gần**

---

## 5) Lưu ý quan trọng

- Nếu ảnh **không phát hiện được mặt**, hệ thống sẽ fallback sang resize cơ bản.
- Ảnh lỗi hoặc không xử lý được sẽ ghi log; nếu bật "Bỏ qua ảnh lỗi" thì batch vẫn tiếp tục.
- Khi thay đổi nhiều thông số, nên bấm **Save Config** để dùng lại lần sau.

---

## 6) File cấu hình chính

Các thiết lập được lưu trong: `photofit-studio/config.json`

Các khóa mới liên quan tự canh chủ thể:

```json
"resize": {
  "auto_subject_fit": true,
  "distance_level": "medium"
}
```

- `auto_subject_fit`: bật/tắt tự canh chủ thể
- `distance_level`: `near` | `medium` | `far`
