import requests
import streamlit as st

def get_local_models(base_url="http://localhost:11434"):
    """Fetch available models from Ollama API."""
    try:
        url = f"{base_url}/api/tags"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            # Extract names and remove potential ':latest' suffix for cleaner UI if desired,
            # but usually it's better to keep the full tag.
            return [m["name"] for m in models_data]
    except Exception:
        pass
    return []

def stream_ollama_response(base_url, model, prompt):
    """Ollama API üzerinden streaming yanıt döner."""
    try:
        import json
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "options": {"temperature": 0.1}
        }
        
        # stream=True ile isteği başlat
        with requests.post(url, json=payload, stream=True, timeout=10) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done"):
                            break
            else:
                yield f"🚨 Hata (Kod {response.status_code}): {response.text}"
    except Exception as e:
        yield f"🚨 Bağlantı Hatası: {str(e)}"
