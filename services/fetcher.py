import requests
from bs4 import BeautifulSoup
import re
import json

URL = "https://www.cnbc.com/ai-artificial-intelligence/"
headers = {"User-Agent": "Mozilla/5.0"}

def fetch_ai_news(max_items=10):
    resp = requests.get(URL, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")

    # Tìm khối script chứa window.__s_data
    script = soup.find("script", string=re.compile(r'window\.__s_data'))
    if not script:
        print("Không tìm thấy dữ liệu nhúng.")
        return []

    # Tìm đoạn JSON lớn (window.__s_data = {...})
    m = re.search(r'window\.__s_data\s*=\s*({.*?});\s*window\.__c_data', script.string, re.DOTALL)
    if not m:
        print("Không match được đoạn json window.__s_data")
        return []

    data = json.loads(m.group(1))
    # Lấy assets từ data['page']['page']['layout'][...]
    # assets nằm ở nhiều module, bạn nên lấy theo module 'twoColumnImageDense', 'threeUpStack', 'river'
    results = []
    try:
        layouts = data["page"]["page"]["layout"]
        for layout in layouts:
            for col in layout.get("columns", []):
                for mod in col.get("modules", []):
                    if mod.get("data", {}).get("assets"):
                        assets = mod["data"]["assets"]
                        for a in assets:
                            title = a.get("title") or a.get("headline")
                            url = a.get("url")
                            desc = a.get("description", "")
                            img = a.get("promoImage", {}).get("url") if a.get("promoImage") else ""
                            date = a.get("datePublished") or a.get("dateLastPublished") or a.get("dateLastPublishedFormattedWithoutTime")
                            results.append({
                                "title": title,
                                "link": url,
                                "desc": desc,
                                "img": img,
                                "date": date
                            })
    except Exception as e:
        print("Parse JSON error:", e)
        return []

    # Loại trùng (theo link)
    seen = set()
    news_list = []
    for n in results:
        if n["link"] not in seen:
            news_list.append(n)
            seen.add(n["link"])
        if len(news_list) >= max_items:
            break
    return news_list

if __name__ == "__main__":
    news_items = fetch_ai_news()
    for n in news_items:
        print(n["title"])
        print(n["link"])
        print("------")