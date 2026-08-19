# Báo Cáo Suy Ngẫm & Kế hoạch Đồ án (Reflection & Action Plan)

**Học viên:** Nguyễn Thị Khánh Ly  
**Khóa học:** AICB-K34 · Track 3: GraphRAG  

---

### 1. Mapping Bài giảng vào Code
| Khái niệm trong bài giảng | Module tương ứng | Hàm / Khối code cụ thể | Quan sát thực tế & Đánh giá |
|--------------------------|------------------|------------------------|-----------------------------|
| **Conservative Coreference** | Module 1 | `resolve_coref_batch()` | Phân giải đại từ theo batch chặt chẽ giúp loại bỏ triệt để các lỗi hallucination từ LLM khi context ngắn. |
| **Schema & Allowlist Guard** | Module 2 | `ALLOWED_NODE_TYPES`, `ALLOWED_RELATIONS` | Giới hạn schema giúp đồ thị sạch, tập trung vào thực thể Company, Person, Technology mà không tạo ra các rác dữ liệu. |
| **Bulk Cypher Ingestion** | Module 2 | `bulk_insert_nodes()`, `bulk_insert_edges()` | Dùng `UNWIND` cải thiện tốc độ ghi dữ liệu lên gấp nhiều lần so với các truy vấn `MERGE` đơn lẻ. |
| **Entity Resolution & Union-Find** | Module 3 | `build_resolution_map()`, `UF` | Thuật toán Union-Find kết hợp Lexical Guard rất hiệu quả trong việc gom nhóm các thực thể bị trùng lặp như MSFT và Microsoft Corp. |
| **Super-node Degree Cap** | Module 4 | `retrieve_graph_context()` | Cắt giảm số lượng láng giềng đối với các hub node (>100 bậc) giữ cho Graph Context Window không bị phình to quá mức giới hạn của LLM. |
| **LLM-as-a-Judge Evaluation** | Module 5 | `judge_answer()` | Việc dùng Prompt tiêu chuẩn để đánh giá Comprehensiveness và Faithfulness cung cấp cái nhìn định lượng rất tốt về RAG Pipeline. |

---

### 2. Quá trình Debugging & Bài học
- **Lỗi kỹ thuật phức tạp nhất gặp phải:** Lỗi encoding khi đọc file và parse JSON output từ LLM trong Extraction step. Trong một số ít trường hợp LLM không trả về strict JSON hoặc bị timeout dẫn tới mất mát cạnh. Thêm vào đó, việc xử lý dữ liệu với file text đôi lúc gặp UnicodeDecodeError trên Windows.
- **Cách bạn đã xử lý thành công:** 
  1. Bổ sung cơ chế `max_retries` với exponential backoff trong hàm gọi LLM (`groq_chat`).
  2. Áp dụng cơ chế kiểm tra kiểu dữ liệu (`isinstance(item, dict)`) để tránh lỗi `AttributeError` khi LLM sinh chuỗi thay vì object.
  3. Cập nhật model từ `openai/gpt-oss-120b` (bị Rate Limit) sang `qwen/qwen3.6-27b` để tăng tốc độ phản hồi và độ ổn định.
  4. Bổ sung cơ chế Auto-Reconnect cho Neo4j (`try-except` khởi tạo lại Driver) để đối phó với lỗi `SSLEOFError` khi query chạy ngầm quá lâu.
  5. Xử lý triệt để lỗi xung đột DLL của PyTorch (`c10.dll` WinError 1114) trên Jupyter Windows bằng cách cấu hình lại Kernel và vá trực tiếp các cơ chế chống văng lỗi vào file `.ipynb` gốc.

---

### 3. Kế hoạch Áp dụng vào Đồ án Thực tế (Action Plan)
- **Tên đồ án / Dự án:** Hệ thống Hỏi đáp Tin tức Tài chính & Quan hệ Doanh nghiệp
- **Đặc thù bài toán & Lý do chọn giải pháp:** Bài toán truy xuất thông tin chuỗi cung ứng và đầu tư chéo giữa các công ty (ví dụ: công ty mẹ - con, đối tác chiến lược) đòi hỏi câu hỏi Multi-hop rất nhiều. Do đó Flat RAG không thể đáp ứng được khi thông tin phân mảnh ở các báo cáo khác nhau. GraphRAG là bắt buộc.
- **Cấu trúc Node & Relation dự kiến:**
  - Nodes: `Company`, `Executive`, `Product`, `MarketSector`
  - Relations: `SUBSIDIARY_OF`, `INVESTED_IN`, `COMPETES_WITH`, `SUPPLIES_TO`, `CEO_OF`
- **Chiến lược xử lý Super-node & Entity Resolution:** Dùng FAISS cho vector similarity kết hợp strict rule (Ticker matching). Đối với các Super-node như các quỹ đầu tư lớn (có hàng nghìn khoản đầu tư), sẽ limit số lượng cạnh dựa trên thời gian và trọng số (confidence) của nguồn trích xuất, hoặc lọc bớt láng giềng bằng Semantic Routing theo Query của người dùng.

---

### 4. Phân tích Kết quả Đánh giá Thực tế (GraphRAG vs Flat RAG)
Dựa trên kết quả chạy pipeline thực tế với tập dữ liệu HackerNoon, dưới đây là so sánh trực tiếp giữa hai phương pháp:

| Metric | Flat RAG | GraphRAG | Chênh lệch (Graph - Flat) |
|---|---|---|---|
| Comprehensiveness (Độ bao phủ) | 3.667 | 4.000 | +0.333 |
| Faithfulness (Độ trung thực) | 3.667 | 4.167 | +0.500 |
| Multi-hop reasoning | 3.500 | 3.500 | 0.000 |
| Latency (Độ trễ - giây) | 14.273 | 13.088 | -1.200 |
| Token usage | 2090.167 | 2241.167 | +151.000 |

**Nhận xét rút ra:**
- **Chất lượng câu trả lời:** GraphRAG vượt trội hơn hẳn về `Comprehensiveness` và đặc biệt là `Faithfulness`. Việc cung cấp context dưới dạng đồ thị tri thức giúp LLM ít bị ảo giác (hallucination) hơn so với việc chỉ nhồi các đoạn text rời rạc từ Flat RAG.
- **Độ trễ (Latency):** Bất ngờ là GraphRAG lại xử lý nhanh hơn (~1.2 giây) ở khâu truy xuất. Điều này có thể giải thích do GraphRAG trích xuất ra các mối quan hệ (triples) súc tích, LLM đọc hiểu nhanh hơn so với đọc một mớ văn bản dài hỗn độn từ Vector DB.
- **Tiêu thụ Token:** GraphRAG tốn token hơn một chút (~150 tokens) do phải chèn thêm các chuỗi biểu diễn đồ thị vào prompt, nhưng hoàn toàn xứng đáng với chất lượng vượt trội.
