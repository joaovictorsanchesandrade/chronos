import base64

semente = "4a080738-c0a2-4905-b404-1100505d7e81,50346315808,17367"
raw = base64.b64encode(semente.encode()).decode()
print(raw)
