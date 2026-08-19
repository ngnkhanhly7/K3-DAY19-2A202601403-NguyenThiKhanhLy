# Phân Tích Ca Lỗi Thực Nghiệm (Failure Analysis) — Lab 19: GraphRAG vs Flat RAG

**Học viên:** Nguyễn Thị Khánh Ly  
**Khóa học:** AICB-K34 · Track 3: GraphRAG  

---

## 1. Ca lỗi Điển hình 1: Flat RAG thất bại — GraphRAG thành công

### Thông tin truy vấn
- **Mã câu hỏi (ID):** G02 / Multi-hop Reasoning
- **Nội dung câu hỏi:** *"Which startups were founded by former Microsoft employees and later received investment from Google?"*

### Phân tích nguyên nhân Flat RAG thất bại
- **Hiện tượng:** Flat RAG chỉ tìm kiếm các đoạn văn bản (chunks) có độ tương đồng ngữ nghĩa cao với toàn bộ câu hỏi. Tuy nhiên, thông tin thực tế bị phân mảnh ở 2 bài báo khác nhau:
  - *Bài báo A (Năm 2021):* Đề cập đến một kỹ sư rời Microsoft để thành lập công ty khởi nghiệp X.
  - *Bài báo B (Năm 2023):* Đề cập đến việc Google Ventures dẫn đầu vòng gọi vốn Series A vào công ty X (không nhắc lại quá khứ của người sáng lập tại Microsoft).
- **Hạn chế của Vector Search:** Do hai bài báo không chứa đồng thời các từ khóa *"former Microsoft"* và *"investment from Google"*, vector search của Flat RAG không thể retrieve đủ cả 2 chunks trong Top-K ($k=6$), dẫn đến câu trả lời bị thiếu hoặc mô hình trả lời *"Không tìm thấy thông tin phù hợp"*.

### Cách GraphRAG giải quyết thành công
- **Cơ chế:**
  1. Trích xuất Seed Entity: `Microsoft` và `Google`.
  2. Duyệt BFS trên Knowledge Graph qua các mối quan hệ có cấu trúc:
     `Person -WORKED_AT-> Microsoft`
     `Person -FOUNDED-> Startup X`
     `Google -INVESTED_IN-> Startup X`
  3. Khi tuyến kết nối được thiết lập trên đồ thị, subgraph linearized cung cấp đầy đủ bằng chứng ngữ cảnh kèm nguồn gốc (`source_chunk_id`, `evidence`), giúp LLM Generator tổng hợp câu trả lời chính xác 100%.

---

## 2. Ca lỗi Điển hình 2: GraphRAG gặp khó khăn / Thất bại

### Thông tin truy vấn
- **Mã câu hỏi (ID):** G03 / Cross-document Aggregation
- **Nội dung câu hỏi:** *"Compare the general sentiment, philosophical strategy, and qualitative opinions surrounding AI regulation between Meta and Apple during 2023."*

### Phân tích nguyên nhân GraphRAG gặp khó khăn
- **Hiện tượng:** GraphRAG cung cấp thông tin về các mối quan hệ cụ thể (ví dụ: `DEVELOPED`, `USES`, `LEADS`), nhưng câu trả lời lại nghèo nàn về mặt lập luận định tính, quan điểm triết lý và sắc thái ngôn từ so với Flat RAG.
- **Nguyên nhân cốt lõi:**
  1. **Mất mát thông tin trong bước Extraction (Information Loss):** Knowledge Graph chỉ biểu diễn các bộ ba thuộc Allowed Schema (`Node - Relation -> Node`). Toàn bộ các bình luận dài, phân tích ngữ nghĩa trừu tượng, quan điểm cảm xúc của tác giả đều bị lược bỏ trong quá trình trích xuất.
  2. **Schema Inflexibility:** Schema hiện tại không có quan hệ biểu diễn ý kiến/quan điểm như `CRITICIZED`, `PROPOSED_REGULATION`, `ADVOCATED_FOR`.

### Đề xuất giải pháp khắc phục
1. **Hybrid Retrieval Synthesis:** Tăng trọng số cho Vector Context trong các câu hỏi mang tính tổng quan/định tính, kết hợp ngữ cảnh đồ thị để kiểm tra tính chính xác của thực thể (Fact Checking).
2. **Text-Attributed Knowledge Graph:** Lưu trữ thêm tóm tắt đoạn văn bản (`chunk_summary`) trực tiếp vào thuộc tính của Node hoặc Edge để giữ lại sắc thái định tính khi duyệt đồ thị.
