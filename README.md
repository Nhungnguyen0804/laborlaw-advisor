# Hướng dẫn cách cài đặt

## Yêu cầu hệ thống

- Python >= 3.11.9
- Docker và Docker Compose
- Git

## Các bước cài đặt

**1. Clone repository**

```bash
git clone https://github.com/Nhungnguyen0804/laborlaw-advisor.git
cd laborlaw-advisor
```

**2. Tạo và kích hoạt virtual environment**

```bash
python -m venv law-env
# Windows
law-env\Scripts\activate
```

**3. Cài đặt dependencies**

```bash
pip install -r requirements.txt
```

**4. Cấu hình biến môi trường**

```bash
cp .env.example .env
```

Mở file `.env` và điền các giá trị trong `.env.example`.

---

# Hướng dẫn triển khai (deploy)

**1. Kích hoạt virtual environment**

```bash

# Windows
law-venv\Scripts\activate
```

**2. Khởi động Neo4j bằng Docker**

```bash
docker compose up -d
```

truy cập Neo4j Browser tại:

```
http://localhost:7474
```

Đăng nhập với thông tin trong file `.env`

# Hướng dẫn chạy thử phần mềm

Mở docker để khởi động Neo4j

Chạy trên terminal:

```bash
E:\laborlaw-advisor\law-env\Scripts\python.exe -m src.main
```

Chạy với giao diện:

```bash
chainlit run app.py
```

# Demo

Câu hỏi cấu trúc pháp lý
![Demo câu hỏi cấu trúc pháp lý và trả lời](demo0.png)

Câu hỏi ngữ nghĩa pháp lý
![Demo câu hỏi ngữ nghĩa pháp lý và trả lời](demo1.png)
![Demo câu hỏi ngữ nghĩa pháp lý và trả lời](demo2.png)
