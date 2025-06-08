import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    def get_int_env(key, default):
        val = os.getenv(key)
        print(f"[DEBUG][config.py] os.getenv({key})={val}")
        if val is None or val.strip() == '':
            return default
        try:
            return int(val)
        except Exception:
            return default
    config = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID"),
        "OLLAMA_API_URL": os.getenv("OLLAMA_API_URL"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
        "MAX_GOOGLE_SEARCH": get_int_env("MAX_GOOGLE_SEARCH", 5),
        "GOOGLE_SEARCH_NUM_RESULTS": get_int_env("GOOGLE_SEARCH_NUM_RESULTS", 8),
        "MAX_SCRAPE_DEPTH": get_int_env("MAX_SCRAPE_DEPTH", 10),
        "SCORE_THRESHOLD": float(os.getenv("SCORE_THRESHOLD", 0.95)),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "MAX_PROCESSING_TIME": get_int_env("MAX_PROCESSING_TIME", 10),
    }
    print(f"[DEBUG][config.py] MAX_PROCESSING_TIME={config['MAX_PROCESSING_TIME']}")
    return config

if __name__ == "__main__":
    # 動作テスト
    cfg = load_config()
    for k, v in cfg.items():
        print(f"{k}: {v}")
