# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** GO HOME
**Thành viên:** 
- Chử Trần Phương Nam - 2A202602675 - Data & Pre-filtering
- Ngụy Khắc Phi Long - 2A202602532 - Benchmark & Evaluation
- Nguyễn Đức Phát - 2A202602753 - Strategy - Chunking Comparator
- Đỗ Thành Đạt - 2A202602874 - Report & Demo
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và Quy định Đại học (Đại học Quốc gia Hà Nội - VNU)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề quy định và dịch vụ của ĐHQGHN vì đây là chủ đề bắt buộc của phân ban K4-L3A. Dữ liệu thực tế phản ánh chính xác các văn bản pháp quy, quy chế xét tuyển, chương trình đào tạo, chính sách học bổng và lịch trình học vụ có cấu trúc bảng biểu phong phú, tính cập nhật cao và phục vụ trực tiếp nhu cầu tra cứu thông tin của sinh viên và cán bộ giảng viên.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chương trình học bổng EVN ĐHQGHN năm học 2025-2026 | https://vnu.edu.vn/dhqghn-thong-bao-chuong-trinh-hoc-bong-evn_dhqghn-nam-hoc-2025-2026-post40521.html | 2026-09-19 / 2025-2026 | 3.745 | audience: student, department: student-affairs, category: scholarship |
| 2 | Phương thức tuyển sinh năm 2026 của Trường ĐH Khoa học Tự nhiên | https://vnu.edu.vn/nam-2026-truong-dh-khoa-hoc-tu-nhien-dhqghn-tuyen-2510-chi-tieu-cho-28-nganh-dao-tao-post40194.html | 2026-09-19 / 2026.1 | 2.474 | audience: student, department: academic-affairs, category: admission |
| 3 | Danh mục các chương trình đào tạo bậc đại học tại ĐHQGHN | https://vnu.edu.vn/dao-tao/chuong-trinh-dao-tao-bac-dai-hoc | 2026-09-19 / 2026.1 | 10.387 | audience: student, department: academic-affairs, category: academic-program |
| 4 | Lịch trình và kế hoạch đào tạo năm học 2025-2026 của ĐHQGHN | https://vnu.edu.vn/dao-tao/ke-hoach-hoc-tap-va-giang-day | 2026-09-19 / 2025-2026 | 3.720 | audience: student, department: academic-affairs, category: academic-calendar |
| 5 | Chương trình trao đổi kỳ Xuân 2027 tại Đại học Osaka, Nhật Bản | https://vnu.edu.vn/chuong-trinh-trao-doi-ky-xuan-2027-tai-dai-hoc-osaka-nhat-ban-post40540.html | 2026-09-19 / 2026.1 | 2.158 | audience: student, department: international-relations, category: exchange |
| 6 | Thống kê đội ngũ cán bộ giảng viên theo chức danh khoa học | https://vnu.edu.vn/can-bo/so-lieu-thong-ke/theo-chuc-danh-khoa-hoc-va-trinh-do-dao-tao | 2026-09-19 / 2026.1 | 4.220 | audience: faculty, department: human-resources, category: faculty-staff |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] Ràng buộc L3A: Tập tài liệu có 2 giá trị `audience` khác nhau (`student`: 5 file, `faculty`: 1 file) phục vụ metadata filtering.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `hoc-bong-evn` | Định danh tài liệu nguồn duy nhất, dùng trong việc xác minh và gỡ lỗi truy xuất. |
| `audience` | string | `student` / `faculty` | Phân cấp đối tượng tiếp nhận thông tin; ngăn chặn việc người học tra nhầm quy chế nội bộ của cán bộ/giảng viên. |
| `department` | string | `academic-affairs` | Giúp thu hẹp không gian tìm kiếm về đúng phòng ban chức năng (Đào tạo, CTSV, Hợp tác quốc tế, Nhân sự). |
| `category` | string | `scholarship`, `admission` | Phân loại chủ đề nghiệp vụ giúp lọc nhanh các tài liệu cùng nhóm chủ đề. |
| `document_version` | string | `2025-2026`, `2026.1` | Đảm bảo tính pháp lý và phiên bản hiệu lực của văn bản quy phạm. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu đại diện:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `hoc-bong-evn.md` | FixedSizeChunker (`fixed_size`) | 15 | 189.0 | Bị cắt ngang các câu quy định điều kiện hồ sơ. |
| `hoc-bong-evn.md` | SentenceChunker (`by_sentences`) | 5 | 505.2 | Giữ trọn câu nhưng các đoạn điều khoản bị dài. |
| `hoc-bong-evn.md` | RecursiveChunker (`recursive`) | 20 | 126.0 | Rất tốt, giữ nguyên các đoạn phân cách dòng đôi. |
| `phuong-thuc-xet-tuyen-hus.md` | FixedSizeChunker (`fixed_size`) | 9 | 196.6 | Cắt đứt mã phương thức (301, 401...) ở mép cắt. |
| `phuong-thuc-xet-tuyen-hus.md` | SentenceChunker (`by_sentences`) | 4 | 396.2 | Tốt cho văn bản dạng gạch đầu dòng ngắn. |
| `phuong-thuc-xet-tuyen-hus.md` | RecursiveChunker (`recursive`) | 11 | 144.5 | Tối ưu, tách gọn từng phương thức xét tuyển riêng biệt. |
| `ke-hoach-dao-tao-nam-hoc.md` | FixedSizeChunker (`fixed_size`) | 16 | 192.7 | Làm vỡ các dòng bảng markdown (table rows). |
| `ke-hoach-dao-tao-nam-hoc.md` | SentenceChunker (`by_sentences`) | 1 | 2780.0 | Thất bại vì bảng không có dấu chấm kết thúc câu. |
| `ke-hoach-dao-tao-nam-hoc.md` | RecursiveChunker (`recursive`) | 17 | 162.5 | Tách theo từng dòng `\n`, giữ trọn từng mốc thời gian. |

### Chiến lược của từng thành viên

**Thành viên 1 — Chử Trần Phương Nam (MSSV: 2A202602675)**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=400`)
- **Mô tả & lý do chọn cho chủ đề này:** Phù hợp nhất cho văn bản quy định và bảng biểu của trường đại học vì ưu tiên cắt theo `\n\n` và `\n` trước khi chia nhỏ theo ký tự, giúp từng dòng bảng biểu hoặc từng điều khoản không bị vỡ vụn.

**Thành viên 2 — Ngụy Khắc Phi Long (MSSV: 2A202602532)**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=200, overlap=50`)
- **Mô tả & lý do chọn:** Chiến lược chia đều truyền thống có overlap 50 ký tự để hạn chế mất thông tin ở biên giới cắt giữa hai chunk liên tiếp.

**Thành viên 3 — Nguyễn Đức Phát (MSSV: 2A202602753)**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Nhóm các câu hoàn chỉnh lại với nhau để giữ toàn vẹn ngữ pháp câu văn bản thông báo học vụ.

**Thành viên 4 — Đỗ Thành Đạt (MSSV: 2A202602874)**
- **Loại chiến lược:** Heading / Section-based Chunker (`chunk_size=500`)
- **Mô tả & lý do chọn:** Tách văn bản theo các mục lớn (`#`, `##`, `###`), gắn kèm tiêu đề mục vào từng chunk con để bảo tồn ngữ cảnh trọn vẹn của từng điều khoản quy chế.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phương Nam | RecursiveChunker (400) | 10/10 | Giữ trọn cấu trúc bảng biểu và phân đoạn điều khoản; chunk gọn gàng. | Cần embedding model ngữ nghĩa tốt để tối ưu score. |
| Phi Long | FixedSizeChunker (200/50) | 6/10 | Kích thước đồng đều, kiểm soát bộ nhớ tốt; overlap chống đứt từ tốt. | Cắt đôi dòng bảng markdown khiến bảng mất tiêu đề cột. |
| Đức Phát | SentenceChunker (3 câu) | 4/10 | Câu văn mạch lạc, ngữ nghĩa hoàn chỉnh. | Không hiệu quả với bảng biểu do bảng không chứa dấu chấm ngắt câu. |
| Thành Đạt | Heading-based Chunker | 8/10 | Giữ nguyên vẹn toàn bộ 1 điều khoản pháp lý trọn vẹn ngữ nghĩa. | Các section bảng biểu quá dài dễ vượt ngưỡng embedding context. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** là chiến lược tối ưu nhất cho văn bản quy chế và dịch vụ đại học. Lý do là văn bản đại học chứa nhiều danh sách tiêu chuẩn và bảng dữ liệu (ngành học, số liệu nhân sự, lịch trình đào tạo). RecursiveChunker ưu tiên ranh giới xuống dòng (`\n\n`, `\n`) trước, giúp giữ nguyên vẹn từng hàng dữ liệu và từng đề mục mà không làm rách cấu trúc thông tin.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên năm thứ mấy và cần đạt kết quả học tập thế nào để đủ điều kiện xét học bổng EVN? | Sinh viên năm thứ 3 các ngành năng lượng, kỹ thuật; kết quả học tập 2025-2026 đạt loại giỏi trở lên, rèn luyện tốt, chưa nhận học bổng ngoài ngân sách khác. | `hoc-bong-evn#0` hoặc `#1` |
| 2 | Thời gian nghỉ Tết Nguyên đán năm học 2025-2026 của sinh viên chính quy kéo dài từ ngày nào đến ngày nào? | Nghỉ Tết Nguyên đán từ ngày 09/02/2026 đến ngày 22/02/2026. | `ke-hoach-dao-tao-nam-hoc#6` |
| 3 | Phương thức 2 của Trường ĐH Khoa học Tự nhiên năm 2026 áp dụng nhân hệ số 2 môn Toán cho những ngành nào? | Môn Toán nhân hệ số 2 đối với các ngành: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu. | `phuong-thuc-xet-tuyen-hus#0` |
| 4 | Chương trình trao đổi sinh viên tại Đại học Osaka kỳ Xuân 2027 có bao nhiêu chỉ tiêu và yêu cầu điểm GPA tối thiểu là bao nhiêu? | Có 03 chỉ tiêu dành cho sinh viên/học viên ĐHQGHN; yêu cầu hoàn thành ít nhất 02 học kỳ và GPA từ 3,2/4,0 trở lên. | `trao-doi-sinh-vien-osaka#0` |
| 5 | [Filter: student] Số lượng và danh mục các chương trình đào tạo chuẩn và đặc thù của Trường Đại học Công nghệ là gì? | Bao gồm 18 chương trình đào tạo (CNTT, CNTT CLC, Robot, Năng lượng, Cơ kỹ thuật, AI...). | `chuong-trinh-dao-tao-dai-hoc#0` đến `#2` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Điều kiện học bổng EVN | RecursiveChunker | CÓ | Recursive giữ trọn vẹn đoạn tiêu chuẩn xét chọn. |
| 2 | Thời gian nghỉ Tết 2026 | RecursiveChunker | CÓ | SentenceChunker thất bại vì bảng lịch trình không có dấu chấm. |
| 3 | Môn Toán nhân đôi HUS | Recursive / FixedSize | CÓ | Chứa đầy đủ danh sách 4 ngành kỹ thuật/toán. |
| 4 | Chỉ tiêu & GPA ĐH Osaka | RecursiveChunker | CÓ | Đoạn điều kiện GPA 3.2 và 3 chỉ tiêu được gom trọn vẹn. |
| 5 | Ngành học ĐH Công nghệ | RecursiveChunker (có filter) | CÓ | Bắt buộc phải có `metadata_filter` để loại bỏ bảng giảng viên. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất hữu ích, thể hiện rõ nhất ở Câu hỏi 5.** Khi không sử dụng filter, câu truy vấn về *"Trường Đại học Công nghệ"* dễ bị lẫn với bảng thống kê nhân sự của cán bộ/giảng viên (`co-cau-doi-ngu-can-bo-giang-vien.md` - audience: faculty). Khi áp dụng `metadata_filter={"audience": "student"}`, hệ thống tiền lọc (pre-filter) loại bỏ 100% các tài liệu nhân sự nội bộ, đảm bảo chỉ truy xuất từ tài liệu chương trình đào tạo của sinh viên.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Sự thất bại của SentenceChunker trên dữ liệu dạng bảng:** Bảng biểu quy chế đại học không có dấu kết thúc câu (`.`), khiến `SentenceChunker` coi cả bảng 3.000 ký tự là 1 câu duy nhất hoặc cắt sai hoàn toàn.
2. **Giá trị thực tiễn của Metadata Pre-Filtering:** Metadata không chỉ để quản lý dữ liệu mà là công cụ định hướng retrieval sống còn khi hệ thống chứa nhiều tài liệu trùng từ khóa nhưng khác đối tượng độc giả.
3. **Giới hạn của MockEmbedder (Hash-based):** Điểm cosine similarity của mock embedder không phản ánh ngữ nghĩa học sâu, chứng minh vì sao trong thực tế cần các mô hình sentence embedding chuyên dụng.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ dữ liệu, nhưng việc chọn chiến lược chunking sai lầm (như cắt câu trên bảng dữ liệu hoặc cắt kích thước cứng làm xé lẻ bảng điểm/tiêu chuẩn) sẽ phá hỏng hoàn toàn khả năng trả lời của LLM phía sau dù LLM có thông minh đến đâu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ triển khai một `MarkdownTableChunker` chuyên dụng để chuyển đổi từng hàng của bảng kèm theo tiêu đề cột (header-aware table row chunking), và tích hợp một semantic embedding model nhẹ chạy on-device (như `bge-small-en` hoặc `phobert`) thay vì chỉ dùng mock hash.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
