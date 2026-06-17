# Lab 16 Benchmark Report

## 1. Thông tin cấu hình (Metadata)

| Cấu hình (Metadata Key) | Thông tin chi tiết (Value) |
| :--- | :--- |
| **Dataset (Tập dữ liệu)** | `hotpot_extended.json` (100 câu hỏi multi-hop) |
| **Execution Mode (Chế độ chạy)** | `llm` (Gọi API OpenAI trực tiếp) |
| **LLM Model (Mẫu ngôn ngữ)** | `gpt-4o-mini` |
| **Total Records (Tổng số bản ghi)** | 200 bản ghi (100 ReAct + 100 Reflexion) |
| **Agents Evaluated (Các Agent)** | `react`, `reflexion` |

---

## 2. So sánh Phương pháp Hoạt động (Methodology Comparison)

| Đặc tính so sánh | Phương pháp 1: ReAct Agent | Phương pháp 2: Reflexion Agent |
| :--- | :--- | :--- |
| **Cơ chế thực thi** | Chạy một lượt duy nhất (One-shot). | Chạy theo vòng lặp sửa lỗi (Actor - Evaluator - Reflector). |
| **Lượt thử tối đa** | 1 lượt duy nhất (`max_attempts = 1`). | Tối đa 3 lượt (`max_attempts = 3`). |
| **Khả năng tự kiểm tra** | Không có. Tin tưởng hoàn toàn vào kết quả của lượt suy luận đầu tiên. | Có Evaluator chấm điểm và phân tích lỗi sai dựa trên đáp án đúng. |
| **Khả năng tự sửa đổi** | Không có bộ nhớ phản hồi lỗi. | Có Reflector đúc kết bài học (`lesson`) và đề xuất chiến thuật (`next_strategy`) ghi vào `reflection_memory`. |
| **Nhược điểm chính** | Độ chính xác bị hạn chế ở câu hỏi khó đòi hỏi liên kết thông tin phức tạp. | Latency và Token tiêu thụ tăng theo số lần thử khi Agent đoán sai. |

---

## 3. Bảng kết quả chạy thực tế (Benchmark Results)

| Chỉ số hiệu năng (Metric) | ReAct Agent | Reflexion Agent | Độ lệch (Delta) | Nhận xét & Ý nghĩa |
| :--- | :---: | :---: | :---: | :--- |
| **Độ chính xác (Exact Match)** | 67.00% | **86.00%** | **+19.00%** | **Reflexion cải tiến vượt trội, tăng 19% tỉ lệ đáp án đúng.** |
| **Lượt thử TB (Attempts)** | 1.0000 | 1.4900 | +0.4900 | Reflexion chạy thêm trung bình 0.49 lượt thử cho các câu hỏi bị sai. |
| **Tokens TB (Tokens/câu)** | 1,869.72 | 3,658.34 | +1,788.62 | Tiêu thụ thêm 1.7K tokens/câu cho khâu Evaluator và Reflector. |
| **Thời gian chạy TB (ms)** | 5,108.87 ms | **4,863.73 ms** | **-245.14 ms** | Tốc độ xử lý tương đương (nhờ tối ưu hóa caching và phản hồi API). |

---

## 4. Ước tính Chi Phí Thực Thi (Cost Estimation)

### Bảng cấu hình giá Token (gpt-4o-mini):
| Loại Token | Đơn giá / 1 Triệu Tokens | Tỉ lệ phân bổ ước tính | Đơn giá trung bình tương đương |
| :--- | :---: | :---: | :---: |
| **Input Token** | $0.15 | 80% | $0.12 |
| **Output Token** | $0.60 | 20% | $0.12 |
| **Tổng cộng** | - | 100% | **$0.24 / 1M Tokens** |

### Bảng chi phí thực tế cho 100 câu hỏi:
| Agent | Tổng số Tokens tiêu thụ | Chi phí ước tính (100 câu) | Chi phí trung bình / câu |
| :--- | :---: | :---: | :---: |
| **ReAct Agent** | 186,972 tokens | **$0.0449** | $0.00045 |
| **Reflexion Agent** | 365,834 tokens | **$0.0878** | $0.00088 |
| **Tổng cộng Benchmark** | **552,806 tokens** | **$0.1327** | **$0.00066** |

---

## 5. Phân tích các loại lỗi (Failure Modes Analysis)

Thống kê chi tiết các lỗi xuất hiện trên 100 câu hỏi (không tính trường hợp trả lời đúng):

| Loại lỗi (Failure Mode) | Lỗi ở ReAct | Lỗi ở Reflexion | Phân tích nguyên nhân & Hướng giải quyết |
| :--- | :---: | :---: | :--- |
| **Incomplete Multi-Hop** (Thiếu hop thông tin) | 31 | **1** | ReAct dừng suy luận sớm ở thực thể thứ nhất. Reflexion sửa đổi thành công 30/31 trường hợp nhờ được chỉ ra phần bằng chứng thiếu. |
| **Entity Drift** (Trôi lệch thực thể) | 2 | **0** | ReAct bị nhiễu thông tin giữa các thực thể tên gần giống nhau. Reflexion giải quyết triệt để lỗi này nhờ so khớp của Evaluator. |
| **Looping** (Bị kẹt vòng lặp) | 0 | **13** | Xảy ra khi Actor lặp lại đáp án sai cũ. Cần cải tiến Reflector để sinh ra các chỉ dẫn bẻ gãy lối suy luận sai lầm trước đó. |
| **Wrong Final Answer** (Sai đáp án) | 0 | 0 | Không có lỗi sai thuần túy nào khác ngoài lỗi trôi lệch thực thể và kẹt vòng lặp. |

---

## 6. Các Extensions đã triển khai (Implemented Extensions)

| Tên Extension | Mô tả chi tiết | Mục tiêu đạt được |
| :--- | :--- | :--- |
| **structured_evaluator** | Sử dụng phản hồi có cấu trúc JSON từ Evaluator. | Đảm bảo tính nhất quán và dễ dàng xử lý đầu ra bằng Pydantic. |
| **reflection_memory** | Lưu trữ nhật ký sửa sai dưới dạng danh sách chỉ dẫn qua các lượt. | Actor sử dụng để điều hướng suy luận tránh lặp lại vết xe đổ. |
| **benchmark_report_json** | Xuất báo cáo tự động ra định dạng JSON. | Phục vụ trực quan hóa dữ liệu lên Dashboard HTML thời gian thực. |
| **mock_mode_for_autograding** | Tích hợp chế độ chạy Mock chuyển đổi linh hoạt bằng cờ lệnh. | Đảm bảo tính kiểm thử nhanh và chấm điểm tự động không tốn chi phí API. |

---

## 7. Thảo luận & Đánh giá (Discussion Analysis Table)

| Khía cạnh đánh giá (Aspect) | Phân tích & Đánh giá chi tiết (Detailed Analysis) |
| :--- | :--- |
| **Hiệu quả cải tiến độ chính xác** | Kiến trúc **Reflexion** mang lại hiệu quả vượt trội trên tập dữ liệu HotpotQA multi-hop với mức cải tiến độ chính xác Exact Match tăng lên tới **19.00%** so với ReAct. |
| **Khả năng khắc phục lỗi** | Cơ chế tự đánh giá lỗi và đề xuất chiến thuật mới giúp giải quyết gần như hoàn toàn lỗi thiếu bước suy luận (`Incomplete Multi-Hop`), giảm từ 31 xuống chỉ còn 1 trường hợp. |
| **Đánh đổi về tài nguyên** | Cải tiến độ chính xác đi kèm việc gia tăng chi phí token **gấp đôi** (từ 186K lên 365K tokens cho 100 câu hỏi) làm tăng chi phí vận hành. |
| **Rủi ro kẹt vòng lặp (Looping)** | Reflexion xuất hiện 13 lỗi kẹt vòng lặp khi Actor lặp đi lặp lại đáp án sai cũ bất chấp sự hướng dẫn từ Reflector. |
| **Đề xuất hướng phát triển** | Cần tập trung tối ưu hóa Prompts của Reflector để sinh ra các chiến thuật đa dạng hơn khi phát hiện Actor bị lặp câu trả lời nhằm bẻ gãy vòng lặp sai lầm. |

