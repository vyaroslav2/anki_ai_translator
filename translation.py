import json
import urllib.request
import ssl
from aqt import mw

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def list_available_models():
    """Debug function to find out what models this API key can see."""
    config = mw.addonManager.getConfig(__name__)
    api_key = config.get("gemini_api_key")
    
    # We check v1beta first as it usually shows the most models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            models = [m['name'] for m in res_data.get('models', [])]
            return "\n".join(models)
    except Exception as e:
        return f"Error listing models: {str(e)}"

def translate_via_gemini(text):
    config = mw.addonManager.getConfig(__name__)
    api_key = config.get("gemini_api_key")
    model = config.get("model_name", "gemini-1.5-flash")
    
    if not api_key: return "Error: No API Key"

    # Try v1beta as it is generally more permissive for newer models
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": f"{config.get('prompt_prefix')} {text}"}]}]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, context=get_ssl_context(), timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        # If we get a 404, let's automatically try to suggest available models
        if e.code == 404:
            available = list_available_models()
            return f"Error 404: Model '{model}' not found.\n\nYour key has access to:\n{available}"
        return f"HTTP Error {e.code}: {err_body}"
    except Exception as e:
        return f"General Error: {str(e)}"