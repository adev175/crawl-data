import openai

def summarize_news_with_ai(news_items, api_key, model="gpt-3.5-turbo"):
    openai.api_key = api_key
    # Ghép prompt:
    prompt = "Dưới đây là các tin tức AI mới nhất hôm nay:\n\n"
    for idx, item in enumerate(news_items, 1):
        prompt += f"{idx}. {item['title']} ({item['date']})\n{item['desc']}\n\n"
    prompt += (
        "Hãy tóm tắt các tin trên thành một bản tin tổng hợp, nêu bật 2-3 sự kiện quan trọng nhất, nhận xét xu hướng nổi bật nếu có."
    )
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=600
    )
    return response['choices'][0]['message']['content']