import requests
import json

url = 'http://119.63.197.152:8903/v1/chat/completions'

headers = {
    'Content-Type': 'application/json'
}

data = {
    "model": "/root/deepseek/",
    "messages": [
        {
            "content": "给我从1数到100",
            "role": "user"
        }
    ],
    "temperature": 0,
    "max_tokens": 4000,
    "stream": True
}

with requests.post(url, headers=headers, json=data, stream=True) as response:
    if response.encoding is None:
        response.encoding = 'utf-8'

    for line in response.iter_lines(decode_unicode=True):
        if line:
            # 处理每一行数据
            if '[DONE]' == line.split(': ')[1]:
                print("")
                print("[Done]")
                print("")
                break

            content = json.loads(line.split(': ')[1])['choices'][0]['delta']['content']

            if '<think>' == content:
                # 深度思考开始
                print("")
                print("[深度思考中]")
                print("")

            elif '</think>' == content:
                # 深度思考结束，输出正文
                print("")
                print("[结束思考]")
                print("")

            print(content, end="")