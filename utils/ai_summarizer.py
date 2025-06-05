import google.generativeai as genai
import os

def summarize_news_with_gemini(news_items, api_key=None):
    """
    Gọi Gemini để tóm tắt và phân tích list news_items (list dict).
    Trả về chuỗi tổng hợp.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-pro')
    # Làm prompt
    prompt = "Đây là danh sách các tin tức về AI mới nhất hôm nay:\n\n"
    for idx, item in enumerate(news_items, 1):
        prompt += f"{idx}. {item['title']} ({item.get('date','')})\n{item.get('desc','')}\n\n"
    prompt += (
        "Hãy tóm tắt các tin trên thành một bản tổng hợp ngắn gọn, nêu bật 2-3 sự kiện quan trọng nhất, nhận xét xu hướng nổi bật nếu có. Viết bằng tiếng Việt, ngắn gọn, dễ hiểu."
    )
    response = model.generate_content(prompt)
    return response.text.strip()