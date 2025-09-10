import requests
from config import PERPLEXITY_API_KEY, PERPLEXITY_API_URL

url = PERPLEXITY_API_URL

headers = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "sonar",
    "messages": [
        {"role": "user", "content": "Hello Perplexity, is my API working?"}
    ]
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    try:
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        print("Assistant Reply:", reply)
    except Exception as e:
        print("Error parsing response:", e, response.text)
else:
    print("Error:", response.status_code, response.text)
