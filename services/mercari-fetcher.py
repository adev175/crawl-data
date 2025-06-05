import requests

url = "https://api.mercari.jp/services/affiliate/user/v1/current_user"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
}

payload = {
    "page_token": "",
    "limit": 120,
    "item_conditions": [],
    "price_min": 0,
    "price_max": 40000,         # Ví dụ: tối đa 40000 yên
    "sort": "created_time",
    "order": "desc",
    "exclude_keyword": "ジャンク",  # Loại trừ từ "ジャンク"
    # "category_id": "859",     # (Nếu có)
    # "brand_id": "3272",       # (Nếu có)
    "keyword": "",              # (Có thể để trống hoặc nhập từ khóa)
}

r = requests.post(url, headers=headers, json=payload)
data = r.json()

for item in data["data"]["items"]:
    print("Tên sản phẩm:", item["name"])
    print("Giá:", item["price"])
    print("Ảnh:", item["thumbnails"][0]["url"])
    print("Link:", f'https://mercari.com/jp/items/{item["id"]}/')
    print("-" * 40)