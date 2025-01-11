# Yahoo Checker

Phần mềm miễn phí được cung cấp bởi [CheckerCCV](https://checkerccv.tv/).

Một script kiểm tra trạng thái tài khoản email Yahoo.

## Yêu cầu

1. Cài đặt Python (nếu chưa cài đặt):
   - [Tải Python tại đây](https://www.python.org/downloads/)
   - Đảm bảo thêm Python vào PATH khi cài đặt.

## Hướng dẫn cài đặt

### Bước 1: Cài đặt các thư viện yêu cầu

```bash
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị danh sách proxy

- Tạo tệp `proxy.txt` trong cùng thư mục với script.
- Thêm proxy vào tệp `proxy.txt` với các định dạng sau:
  - `username:password@host:port`
  - `host:port`
- **Lưu ý:** Mỗi proxy phải nằm trên một dòng.

### Bước 3: Chuẩn bị danh sách email

- Tạo tệp `Mail.txt` trong cùng thư mục với script.
- Thêm email Yahoo vào `Mail.txt`, mỗi email trên một dòng. Ví dụ:
  ```
  example@yahoo.com
  example2@yahoo.com:password
  example3@yahoo.com|password
  ```

### Bước 4: Chạy script

1. Chạy script `create_session.py` với số luồng bạn mong muốn:

```bash
python create_session.py
```

Ví dụ: Nhập số luồng là `5` khi được yêu cầu.

2. Tiếp theo, chạy script `yahoo_checker.py` với số luồng gấp 3 lần số threads đã sử dụng trong `create_session.py`:

```bash
python yahoo_checker.py
```

Ví dụ: Nếu bạn đã sử dụng 5 threads ở `create_session.py`, hãy nhập `15` threads khi chạy `yahoo_checker.py`.

### Lưu ý
- Đảm bảo thư mục `session` tồn tại trong cùng thư mục nếu script sử dụng tệp session.
- Tránh trùng lặp email trong `Mail.txt` vì các bản trùng lặp sẽ được tự động loại bỏ.
