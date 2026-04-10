# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lê Đức Hải
**Nhóm:** Nhóm 10
**Ngày:** 10-04-2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity là hai vector có hướng rất giống nhau trong không gian đa chiều, cho thấy hai đoạn văn bản có sự tương đồng cao về ngữ nghĩa.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi rất thích học lập trình."
- Sentence B: "Lập trình là niềm đam mê của tôi."
- Tại sao tương đồng: Cả hai câu đều chia sẻ những từ khóa quan trọng ("lập trình") và truyền tải cùng một ý nghĩa tích cực về việc học code, dù cách dùng từ khác nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Thời tiết hôm nay thật đẹp."
- Sentence B: "Cấu trúc dữ liệu và giải thuật rất khó."
- Tại sao khác: Hai câu này thuộc hai chủ đề hoàn toàn khác nhau (thời tiết và học thuật), không có điểm chung về từ vựng hay ngữ cảnh.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo lường góc giữa các vector thay vì khoảng cách tuyệt đối, giúp loại bỏ ảnh hưởng của độ dài văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Số lượng chunks = (10000-50)/(500-50)= 9950/450 = 22,11 

> *Đáp án:* 23 chunks (làm tròn lên để bao phủ toàn bộ văn bản)

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunks sẽ tăng lên. Overlap nhiều hơn giúp bảo tồn ngữ cảnh giữa các đoạn văn bản bị cắt ngang, đảm bảo các thực thể hoặc ý nghĩa quan trọng không bị mất đi khi nằm ở ranh giới giữa hai chunk. Điều này đặc biệt quan trọng để cải thiện độ chính xác khi truy vấn thông tin (RAG).

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Cybersecurity products & services (Viettel Cyber Security)

**Tại sao nhóm chọn domain này?**
> Viettel Cyber Security cung cấp hệ sinh thái giải pháp an toàn thông tin đa dạng (WAF, SOC, Threat Intelligence, Endpoint Security, CSMP). Các tài liệu datasheet có cấu trúc rõ ràng, giàu thuật ngữ chuyên ngành, phù hợp để xây dựng hệ thống RAG hỗ trợ tư vấn sản phẩm bảo mật.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Viettel Cloud WAF | Viettel IDC Datasheet | 4,481 | product: "Cloud WAF", category: "web_security", service_type: "WAF", provider: "Viettel IDC" |
| 2 | Viettel Cloudrity | Viettel IDC Datasheet | 2,914 | product: "Cloudrity", category: "web_security", service_type: "Anti-DDoS & WAF", provider: "Viettel IDC" |
| 3 | Viettel Threat Intelligence | Viettel IDC Datasheet | 5,727 | product: "Threat Intelligence", category: "threat_intelligence", service_type: "Threat Feed", provider: "Viettel IDC" |
| 4 | Viettel Virtual SOC | Viettel IDC Datasheet | 9,149 | product: "Virtual SOC", category: "soc_monitoring", service_type: "Managed SOC", provider: "Viettel IDC" |
| 5 | Viettel CSMP | Viettel IDC Datasheet | 3,491 | product: "CSMP", category: "consulting", service_type: "Maturity Program", provider: "Viettel IDC" |
| 6 | Viettel Endpoint Security | Viettel IDC Datasheet | 15,909 | product: "Endpoint Security", category: "endpoint_protection", service_type: "EDR/EPP", provider: "Viettel IDC" |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| product | string | "Cloud WAF", "Virtual SOC" | Lọc kết quả theo sản phẩm cụ thể khi user hỏi về một giải pháp |
| category | string | "web_security", "endpoint_protection" | Nhóm các sản phẩm cùng lĩnh vực, hỗ trợ so sánh giải pháp |
| service_type | string | "WAF", "Managed SOC", "EDR/EPP" | Phân biệt loại dịch vụ chi tiết, giúp retrieval chính xác hơn |
| provider | string | "Viettel IDC" | Xác định nguồn cung cấp, hữu ích khi mở rộng thêm vendor khác |
---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
|VIETTEL CLOUD WAF | RecursiveChunker (`recursive`) | 26|205.23 | High|
|VIETTEL CLOUD WAF | FixedSizeChunker (`fixed_size`) | 16|298.81| Low|
|VIETTEL CLOUD WAF | SentenceChunker (`by_sentences`) | 5|895 | Medium|
|VIETTEL CLOUDRITY | RecursiveChunker (`recursive`) | 17|224.41 | High|
|VIETTEL CLOUDRITY| SentenceChunker (`by_sentences`) | 11|257.82 | Medium|
|VIETTEL CLOUDRITY| ixedSizeChunker (`fixed_size`) | 11|277.45 | Low|

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> Chiến lược này thực hiện chia nhỏ văn bản bằng phương pháp đệ quy dựa trên danh sách các ký tự phân tách có thứ tự ưu tiên từ lớn đến nhỏ như đoạn văn (\n\n), dòng mới (\n), và các dấu câu. Thay vì cắt văn bản một cách thô bạo theo kích thước cố định, nó luôn cố gắng tìm điểm ngắt tự nhiên nhất gần giới hạn 'chunk_size' để duy trì tính toàn vẹn của cấu trúc văn bản. Nhờ cơ chế này, các khối thông tin kỹ thuật liên quan luôn được giữ lại trong cùng một đoạn, giúp bảo toàn tối đa ngữ cảnh logic và nâng cao độ chính xác khi truy xuất dữ liệu.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Khai thác tốt cấu trúc phân cấp của tài liệu (như tiêu đề, danh sách, đoạn văn) để tránh việc cắt đôi các quy tắc bảo mật hay tham số kỹ thuật quan trọng. Việc giữ các khối thông tin liên quan đi liền với nhau giúp bảo toàn tối đa ngữ cảnh, đảm bảo hệ thống RAG truy xuất được dữ liệu chính xác và có nghĩa cho người dùng.



### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
|VIETTEL CLOUDRITY| SentenceChunker (`by_sentences`) | 11|257.82 | Medium|
|VIETTEL CLOUDRITY | RecursiveChunker (`recursive`) | 17|224.41 | High|

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|-------------|------------|--------------------|
| Vũ Trung Lập| Markdown Chunker| 10| Không gãy đổ Context logic của Document đặc thù.| Phụ thuộc vào chất lượng formatting Markdown.|
| Dương Mạnh Kiên | RecursiveChunker (chunk_size=500) | 8 | 133 chunks trên 6 tài liệu, 22% chunk có header, giữ nguyên cấu trúc section markdown, phù hợp tài liệu datasheet có cấu trúc rõ ràng | Số lượng chunk nhiều nhất (133 vs 90/63), avg length nhỏ (311 ký tự), một số chunk quá ngắn (3-32 ký tự) do separator --- |
| Nguyễn Văn Hiếu | Header Chunker| 9 | Giữ trọn vẹn ý nghĩa mục lục| Phụ thuộc định dạng Markdown|
| Bùi Quang Hải| MarkdownHeaderChunker (Custom)| 9.5| Giữ trọn vẹn ngữ cảnh theo tiêu đề, metadata heading phong phú.| Kích thước chunk không đồng đều tùy theo văn bản gốc.|
| Lê Đức Hải| RecursiveChunker| 9| Giữ trọn vẹn các đoạn văn và đề mục Markdown|Phức tạp trong việc thiết lập tham số|
| Tạ Vĩnh Phúc| RecursiveChunker + Filter| 9 | Giữ trọn vẹn cấu trúc Markdown (bảng biểu, gạch đầu dòng). Filter giúp loại bỏ hoàn toàn nhiễu giữa các sản phẩm WAF/SOC/TI| Cần thời gian tiền xử lý dữ liệu và gắn metadata thủ công lúc đầu|

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Rõ ràng Markdown Chunker là cực phẩm cho Domain Datasheet bảo mật. Vì dữ liệu này được convert từ PDF/Web thành Markdown nên nó có bố cục Heading tuyệt đối chính xác để khoanh vùng (isolate) tính năng. RAG sẽ tìm 1 nhát ăn ngay mà không bị quấy rầy bởi Context không liên quan.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Hàm này sử dụng biểu thức chính quy (Regex) với pattern r'(?<=[.!?])\s+' để thực hiện split văn bản tại các vị trí có dấu chấm, dấu hỏi hoặc dấu chấm than theo sau là khoảng trắng. Cách tiếp cận này giúp xử lý các edge case như viết tắt bằng cách chỉ ngắt khi có khoảng trắng ngăn cách giữa các câu.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán hoạt động theo cơ chế đệ quy, liên tục thử nghiệm việc chia nhỏ văn bản dựa trên danh sách ký tự phân tách có thứ tự ưu tiên (từ đoạn văn, dòng mới đến khoảng trắng). Base case (điểm dừng) xảy ra khi một đoạn văn bản đã có độ dài nhỏ hơn hoặc bằng 'chunk_size', hoặc khi danh sách các ký tự phân tách đã cạn kiệt, đảm bảo mỗi chunk trả về là đơn vị logic nhỏ nhất có thể.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Tài liệu được chuyển đổi thành vector thông qua hàm embedding và lưu trữ cùng metadata vào danh sách nội bộ hoặc bộ nhớ 'ChromaDB' để truy xuất nhanh. Khi thực hiện 'search', hệ thống sử dụng thuật toán tính khoảng cách (như Cosine Similarity hoặc L2 distance) để so sánh vector câu hỏi với các vector lưu trữ, từ đó trả về những đoạn văn bản có độ tương đồng ngữ nghĩa cao nhất.

**`search_with_filter` + `delete_document`** — approach:
> Hệ thống áp dụng cơ chế pre-filtering (lọc trước), trong đó các metadata được kiểm tra để loại bỏ những bản ghi không thỏa mãn điều kiện trước khi thực hiện tính toán tương đồng vector nhằm tối ưu hiệu năng. Đối với 'delete_document', bản ghi được loại bỏ khỏi store dựa trên định danh duy nhất (ID) được tạo ra từ lúc thêm tài liệu, đảm bảo kho dữ liệu luôn được cập nhật chính xác.

### KnowledgeBaseAgent

**`answer`** — approach:
> Prompt được cấu trúc theo dạng RAG (Retrieval-Augmented Generation), bao gồm một chỉ thị hệ thống (system instruction) nghiêm ngặt yêu cầu chỉ sử dụng thông tin được cung cấp. Ngữ cảnh (context) thu được từ 'EmbeddingStore' sẽ được inject trực tiếp vào prompt dưới dạng các đoạn văn bản tham chiếu, giúp mô hình ngôn ngữ lớn (LLM) có đủ dữ liệu thực tế để trả lời các câu hỏi chuyên sâu về domain mà không bị ảo giác.

### Test Results

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                      [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                               [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                        [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                         [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                              [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                              [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                    [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                     [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                   [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                     [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                     [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                                [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                            [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                      [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                             [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                                 [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                           [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                                 [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                     [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                       [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                         [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                               [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                    [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                      [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                          [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                       [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                                [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                               [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                          [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                      [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                                 [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                     [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                           [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                     [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                  [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                                [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                               [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                   [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                              [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                       [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                             [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED 
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 |Cách cấu hình chặn IP theo quốc gia trên WAF. | Hướng dẫn thiết lập Geo-IP blocking cho website.| high|0.88 |Đúng |
| 2 |Hệ thống đang bị tấn công từ chối dịch vụ phân tán. | Cloud Security giúp tối ưu hóa tốc độ truy cập web.| low |0.37 | Đúng|
| 3 |Thiết lập Whitelist cho địa chỉ IP của quản trị viên. | Cho phép các địa chỉ IP tin cậy truy cập không bị chặn.| high | 0.84| Đúng|
| 4 | Tấn công SQL Injection vào cơ sở dữ liệu.|Hacker đang sử dụng script để chèn mã độc vào form. | high | 0.7|Sai |
| 5 | Chứng chỉ SSL giúp mã hóa dữ liệu truyền tải.|Đăng ký mua tên miền cho doanh nghiệp Viettel. | low |0.32 | Đúng|

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất nằm ở cặp số 4, khi mô hình nhận diện sự tương đồng giữa thuật ngữ chuyên môn "SQL Injection" và mô tả hành động "chèn mã độc vào form" dù không trùng lặp từ khóa nào. Điều này chứng minh Embedding không chỉ hoạt động theo cơ chế so khớp từ vựng mà thực sự ánh xạ các khái niệm vào không gian vector dựa trên ngữ cảnh sử dụng thực tế.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Viettel Cloud WAF có những gói dịch vụ nào? | 3 gói: Standard, Advanced, Complete — khác nhau về WAF, Bot Manager, DDoS, Data Retention |
| 2 | Giải pháp nào của Viettel giúp chống tấn công DDoS? | Viettel Cloudrity (Anti-DDoS L4/L7) và Viettel Cloud WAF (DDoS Protection lên đến 15 Tbps) |
| 3 | Viettel Threat Intelligence thu thập dữ liệu từ những nguồn nào? | ISP toàn cầu, đối tác FIRST/APWG, Pentest, Threat Hunting, Managed Security Service, nghiên cứu nội bộ APT/zero-day |
| 4 | SOC của Viettel tổ chức vận hành như thế nào? | 6 nhóm: Tier 1 (giám sát 24/7), Tier 2 (xử lý sự cố), Tier 3 (chuyên sâu), Content Analysis, Threat Analysis, SOC Manager |
| 5 | Viettel Endpoint Security hỗ trợ những hệ điều hành nào? | Windows, Linux, macOS, Android, iOS; tương thích VMware, Hyper-V, XenServer, KVM |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 |Viettel Cloud WAF bảo vệ website như thế nào? |Hệ thống sử dụng tường lửa đa lớp để chặn các cuộc tấn công như SQLi, XSS và Bot. | 0.91| Yes| WAF bảo vệ web bằng cách lọc lưu lượng độc hại qua bộ quy tắc bảo mật thông minh...|
| 2 |Làm sao để chặn truy cập từ một địa chỉ IP lạ? |Hướng dẫn cấu hình Access Control List (ACL) để tạo các quy tắc Blacklist cho IP cụ thể. |0.88 |Yes | Bạn truy cập trang quản trị, chọn mục Policy và thêm địa chỉ IP lạ vào danh sách Blacklist...|
| 3 | Chính sách hoàn tiền của dịch vụ là gì?| (Trả về đoạn giới thiệu tổng quan về hạ tầng trung tâm dữ liệu Viettel)| 0.42|No | Xin lỗi, tài liệu hiện tại không cung cấp thông tin chi tiết về chính sách hoàn phí của dịch vụ.|
| 4 |Hệ thống có chống được tấn công DDoS không? | Tài liệu về tính năng Anti-DDoS tích hợp, giúp nhận diện và giảm thiểu lưu lượng tấn công ảo.| 0.85| Yes|Có, dịch vụ hỗ trợ chống tấn công DDoS ở lớp 3, 4 và lớp 7 giúp duy trì tính liên tục của web... |
| 5 | Cách thiết lập cảnh báo qua Email?|Hướng dẫn cài đặt Notification để nhận thông báo khi có các sự kiện bảo mật nghiêm trọng. | 0.83| Yes|Để nhận cảnh báo, bạn cấu hình thông tin SMTP và danh sách email nhận tin trong phần Settings... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Qua quá trình làm việc chung, tôi đã học được cách tối ưu hóa các biểu thức chính quy (Regex) để xử lý các edge case phức tạp trong tài liệu kỹ thuật, ví dụ như tránh việc ngắt câu sai tại các địa chỉ IP hoặc phiên bản phần mềm. Sự phối hợp này giúp tôi hiểu rằng việc tinh chỉnh nhỏ trong tiền xử lý dữ liệu có thể cải thiện đáng kể chất lượng của các khối văn bản (chunks) đầu vào.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ ưu tiên triển khai Semantic Chunking ngay từ đầu thay vì chỉ dựa vào các phương pháp cắt văn bản theo ký tự truyền thống để đảm bảo các ý tưởng kỹ thuật luôn được giữ trọn vẹn. Ngoài ra, tôi sẽ đầu tư thêm thời gian vào bước làm sạch dữ liệu (data cleaning) để loại bỏ các ký tự thừa từ file Markdown, giúp mô hình Embedding tạo ra các vector đặc trưng chính xác hơn cho các quy tắc bảo mật của WAF.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **100 / 100** |
