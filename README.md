# 🤖 Chatbot Hỏi Đáp với Kỹ thuật RAG sử dụng LangChain

Dự án xây dựng chatbot hỗ trợ trả lời câu hỏi dựa trên tài liệu được chỉ định, kết hợp kỹ thuật **RAG (Retrieval-Augmented Generation)** và thư viện **LangChain**.

## 📚 Mô tả

Chatbot có khả năng:

- Đọc hiểu tài liệu PDF.
- Tìm kiếm thông tin liên quan với **VectorStore (FAISS, Chroma,...)**.
- Sinh câu trả lời tự nhiên dựa trên dữ liệu thực tế.
- Hỗ trợ đa mô hình: OpenAI, HuggingFace Transformers, Mistral,...

## 🧰 Công nghệ sử dụng

| Thành phần | Công nghệ                                      |
| ---------- | ---------------------------------------------- |
| Backend    | FastAPI                                        |
| LLM        | OpenRouter (HuggingFace / Mistral / Gemini...) |
| RAG        | LangChain                                      |
| Vector DB  | FAISS/Chroma                                |
| Embedding  | SentenceTransformers                           |

## Dataset

Link Google Drive: https://drive.google.com/drive/folders/1vWZiTOWALQaMjCASfdkpfjk3oo5x3q1A

## 📦 Cài đặt

### Tải source

```bash
git clone https://github.com/watatek/ChatbotAI.git
cd ChatbotAI
```

### Tạo môi trường ảo và kích hoạt

```bash
python -m venv .venv
.\.venv\Script\activate
```

### Update pip

```bash
python -m pip install --upgrade pip
```

### Tải thư viện

```bash
pip install -r requirements.txt
```
