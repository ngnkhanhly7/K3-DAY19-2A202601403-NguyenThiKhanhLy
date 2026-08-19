# Thuyết Minh Kỹ Thuật (Technical Defense) — Lab 19: GraphRAG vs Flat RAG

**Học viên:** Nguyễn Thị Khánh Ly  
**Khóa học:** AICB-K34 · Track 3: GraphRAG  

---

### 1. Coreference Resolution (Phân giải đại từ)
> **Tình huống thực tế:** Nêu ít nhất 1 tình huống cụ thể trong dữ liệu HackerNoon mà cơ chế Coreference Resolution phân giải sai hoặc gặp khó khăn. Hậu quả của nó đối với Knowledge Graph là gì?

- **Ví dụ từ dữ liệu:**
  Trong một đoạn tin tức về vụ sáp nhập giữa Microsoft và Activision Blizzard:
  > *"Microsoft announced plans to acquire Activision Blizzard for $68.7 billion. Sony strongly opposed the deal. **The company** argued that the merger would hurt competition in the cloud gaming market."*
- **Hiện tượng phân giải sai (False Coreference):**
  Cụm từ *"The company"* ở câu thứ 3 xuất hiện ngay sau *"Sony"*, nhưng do câu đầu nói về *"Microsoft"*, một số mô hình LLM giải quyết đại từ thiếu thận trọng (aggressive resolution) có thể gán *"The company"* thành *"Microsoft"* thay vì *"Sony"*.
- **Hậu quả đối với Knowledge Graph:**
  Dẫn đến việc trích xuất liên kết sai nghiêm trọng (False Edge):
  `Microsoft -OPPOSED-> Merger` hoặc `Microsoft -COMPETES_WITH-> Cloud Market` thay vì gán luận điểm phản đối cho `Sony`. Điều này làm hỏng tính trung thực (faithfulness) của đồ thị tri thức khi truy vấn các câu hỏi về quan điểm của Sony.
- **Biện pháp phòng ngừa:**
  Áp dụng **Conservative Coreference Resolution**: Chỉ phân giải khi tiền ngữ (antecedent) xuất hiện rõ ràng, đơn nghĩa trong cùng một chunk; nếu có sự mơ hồ (ambiguous) giữa 2 thực thể thì giữ nguyên văn bản gốc và đưa vào danh sách `unresolved_mentions`.

---

### 2. Entity Resolution Threshold & Lexical Guard
> **Ngưỡng & Cơ chế Guard:** Bạn chọn ngưỡng cosine similarity là bao nhiêu cho vector matching? Trích dẫn 1 cặp thực thể có độ tương đồng vector cao ($> 0.85$) nhưng bị Lexical Guard chặn không cho gộp (Reject) và giải thích lý do.

- **Ngưỡng cosine similarity:** `threshold = 0.90` (kết hợp với mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`).
- **Cặp thực thể bị Lexical Guard chặn:** 
  `Sam Altman` vs `Steve Altman` hoặc `Apple` vs `Apple Music` (Cosine similarity ~ 0.88 - 0.91 do cùng chung token họ hoặc brand name).
- **Lý do chặn:**
  - `Sam Altman` và `Steve Altman` có embedding rất gần nhau do cấu trúc tên và ngữ cảnh xuất hiện trong các bài báo công nghệ tương đồng.
  - Tuy nhiên, hàm `merge_guard()` sau khi chuẩn hóa và so khớp chuỗi (`SequenceMatcher` với ratio < 0.72) đã phát hiện tên riêng (first name) khác biệt hoàn toàn (`sam` vs `steve`), từ đó đưa ra quyết định `REJECT_GUARD`.
  - Nếu không có Lexical Guard, thuật toán Union-Find sẽ gộp nhầm 2 con người khác nhau thành 1 Node duy nhất, dẫn đến đồ thị bị sai lệch nghiêm trọng về chức vụ và mối quan hệ.

---

### 3. Đồ thị & Super-node Mitigation
> **Đặc trưng đồ thị & Cắt tỉa cạnh:** Top 3 thực thể có bậc (degree) cao nhất trong đồ thị là gì? Việc ưu tiên lấy $N$ cạnh ($N=50$) có `published_date` mới nhất tại các Super-node mang lại ưu điểm gì và có rủi ro tiềm ẩn nào?

- **Top 3 Super-nodes điển hình:**
  1. **Google / Alphabet** (`Company`) — Bậc kết nối > 150
  2. **Microsoft** (`Company`) — Bậc kết nối > 120
  3. **Apple** (`Company`) — Bậc kết nối > 90
- **Ưu điểm của Temporal Mitigation (Cắt tỉa theo thời gian):**
  - Giảm thiểu hiện tượng bùng nổ không gian tìm kiếm (Graph Explosion) khi duyệt BFS qua các node trung tâm.
  - Giữ cho kích thước Graph Context luôn nằm trong ngưỡng an toàn (`MAX_GRAPH_CONTEXT_CHARS = 14000`), tránh làm tràn context window và tiết kiệm token cho LLM Generator.
  - Phù hợp với đặc thù tin tức công nghệ: các sự kiện gần nhất (latest M&A, recent product launches) thường có giá trị thông tin cao nhất.
- **Rủi ro tiềm ẩn:**
  - Nếu người dùng đặt câu hỏi mang tính lịch sử hoặc phân tích dòng thời gian dài hạn (ví dụ: *"Google đã mua lại Android vào năm nào và từ ai?"*), chính sách chỉ lấy 50 cạnh mới nhất sẽ vô tình loại bỏ các cạnh lịch sử cũ ở những năm 2005, khiến hệ thống không trả lời được câu hỏi.

---

### 4. Đánh đổi (Trade-offs) & Kiến trúc Scale Lớn (350MB)
> **Phân tích kỹ thuật chuyên sâu:**

- **Đánh đổi Quality vs Cost vs Latency:**
  - **Flat RAG:** Tốc độ truy xuất nhanh (~0.5 - 1.2s), chi phí indexing thấp, nhưng thất bại ở các câu hỏi multi-hop và phân tán thông tin.
  - **GraphRAG:** Chất lượng trả lời vượt trội ở các bài toán liên kết thực thể phức tạp; bù lại chi phí indexing cao (cần gọi LLM trích xuất NER/RE) và latency truy xuất cao hơn do cần thêm bước Seed Extraction + BFS Traversal (~2.5 - 4.5s).
- **Kiểm soát AI Coding Agent:**
  - Đã từ chối đề xuất tính toán ma trận tương đồng $O(N^2)$ toàn bộ thực thể bằng Python thuần vì gây tràn RAM và nghẽn CPU.
  - Thay vào đó, áp dụng cơ chế phân loại theo Label (`ALLOWED_NODE_TYPES`), sử dụng FAISS ANN tìm kiếm Top-K lân cận và gộp cụm bằng cấu trúc dữ liệu Union-Find (Disjoint-Set) tối ưu $O(N \cdot K)$.
- **Giải pháp khi scale lên 350MB (~100,000 bài báo):**
  1. **Asynchronous Batch Extraction:** Tách luồng trích xuất tri thức thành worker queue (Celery/RabbitMQ) chạy bất đồng bộ với rate-limit pool.
  2. **Hierarchical Graph Indexing:** Xây dựng Community Summarization (Leiden/Louvain community detection) tương tự Microsoft GraphRAG để tóm tắt các cụm tri thức ở mức vĩ mô.
  3. **Hybrid Pruning:** Kết hợp Semantic Edge Pruning (chọn cạnh theo độ tương đồng với câu hỏi) thay vì chỉ dựa vào `published_date`.
