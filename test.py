OPEN_AI_KEY = "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"

from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPEN_AI_KEY,
)

request = input("what do you wanna know  ? ")

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  extra_body={},
  model="openai/gpt-oss-safeguard-20b",
  messages=[
              {
                "role": "user",
                "content": request
              }
            ]
)

print(completion.choices[0].message.content)