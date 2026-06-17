# Lab 16 Benchmark Report (Golden Test Set)

## 1. Thông tin cấu hình (Metadata)

| Cấu hình (Metadata Key) | Thông tin chi tiết (Value) |
| :--- | :--- |
| **Dataset (Tập dữ liệu)** | `hotpot_golden.json` (20 câu hỏi Golden Test Set) |
| **Execution Mode (Chế độ chạy)** | `llm` (Gọi API OpenAI trực tiếp) |
| **LLM Model (Mẫu ngôn ngữ)** | `gpt-4o-mini` |
| **Total Records (Tổng số bản ghi)** | 40 bản ghi (20 ReAct + 20 Reflexion) |
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
| **Độ chính xác (Exact Match)** | 90.00% | **95.00%** | **+5.00%** | **Reflexion cải tiến thêm 5%, đạt độ chính xác gần như tuyệt đối (19/20 câu đúng).** |
| **Lượt thử TB (Attempts)** | 1.0000 | 1.2000 | +0.2000 | Reflexion chạy thêm trung bình 0.20 lượt thử cho các câu hỏi bị sai ở lượt đầu. |
| **Tokens TB (Tokens/câu)** | 590.35 | 838.15 | +247.80 | Tiêu thụ thêm 247 tokens/câu cho khâu Evaluator và Reflector. |
| **Thời gian chạy TB (ms)** | 2,363.50 ms | 2,834.80 ms | +471.30 ms | Thời gian chạy tăng thêm 471.3 ms cho quá trình phản chiếu của các câu chưa đúng. |

---

## 4. Ước tính Chi Phí Thực Thi (Cost Estimation)

### Bảng cấu hình giá Token (gpt-4o-mini):
| Loại Token | Đơn giá / 1 Triệu Tokens | Tỉ lệ phân bổ ước tính | Đơn giá trung bình tương đương |
| :--- | :---: | :---: | :---: |
| **Input Token** | $0.15 | 80% | $0.12 |
| **Output Token** | $0.60 | 20% | $0.12 |
| **Tổng cộng** | - | 100% | **$0.24 / 1M Tokens** |

### Bảng chi phí thực tế cho 20 câu hỏi Golden Set:
| Agent | Tổng số Tokens tiêu thụ | Chi phí ước tính (20 câu) | Chi phí trung bình / câu |
| :--- | :---: | :---: | :---: |
| **ReAct Agent** | 11,807 tokens | **$0.00283** | $0.00014 |
| **Reflexion Agent** | 16,763 tokens | **$0.00402** | $0.00020 |
| **Tổng cộng Benchmark** | **28,570 tokens** | **$0.00685** | **$0.00034** |

---

## 5. Phân tích các loại lỗi (Failure Modes Analysis)

Thống kê chi tiết các lỗi xuất hiện trên 20 câu hỏi Golden Set (không tính trường hợp trả lời đúng):

| Loại lỗi (Failure Mode) | Lỗi ở ReAct | Lỗi ở Reflexion | Phân tích nguyên nhân & Hướng giải quyết |
| :--- | :---: | :---: | :--- |
| **Incomplete Multi-Hop** (Thiếu hop thông tin) | 2 | **1** | ReAct bị thiếu thông tin ở thực thể thứ hai. Reflexion sửa đổi thành công 1 trường hợp nhờ chỉ dẫn từ Reflector, chỉ còn 1 câu chưa đúng. |
| **Entity Drift** (Trôi lệch thực thể) | 0 | 0 | Không ghi nhận lỗi trôi lệch thực thể trên bộ dữ liệu này. |
| **Looping** (Bị kẹt vòng lặp) | 0 | 0 | Không ghi nhận hiện tượng kẹt vòng lặp trên bộ dữ liệu này. |
| **Wrong Final Answer** (Sai đáp án) | 0 | 0 | Không có lỗi sai nào khác. |

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
| **Hiệu quả cải tiến độ chính xác** | Trên bộ dữ liệu Golden Test Set, kiến trúc **Reflexion** nâng độ chính xác từ **90.00%** lên tới **95.00%** (chỉ sai 1 câu duy nhất trên tổng số 20 câu). |
| **Khả năng khắc phục lỗi** | Sửa sai thành công 50% lỗi thiếu suy luận (`Incomplete Multi-Hop`) so với ReAct chỉ qua thêm trung bình 0.2 lượt thử. |
| **Đánh đổi về tài nguyên** | Chi phí token và thời gian chạy tăng nhẹ (lần lượt tăng 247.8 tokens và 471.3 ms mỗi câu hỏi), hoàn toàn xứng đáng với mức cải tiến độ chính xác thu được. |
| **Đánh giá chung** | Bộ tham số và prompts của hệ thống hoạt động cực kỳ ổn định trên bộ dữ liệu kiểm thử mới (Golden Set), khẳng định tính tổng quát hóa cao của agent. |
