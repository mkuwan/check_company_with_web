import os
import subprocess
import time
import re
from config import load_config

# テスト用に.envを書き換える関数
def set_env_value(key, value):
    lines = []
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(f'{key}='):
                lines.append(f'{key}={value}\n')
            else:
                lines.append(line)
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(lines)

def test_max_processing_time_reflect():
    """
    .envのMAX_PROCESSING_TIME=3で3秒でタイムアウトするか確認
    """
    set_env_value('MAX_PROCESSING_TIME', '3')
    start = time.time()
    proc = subprocess.Popen(['python', 'main.py', '--company', 'A', '--address', 'B', '--tel', 'C'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        assert False, 'プロセスが5秒以内に終了しませんでした'
    elapsed = time.time() - start
    assert proc.returncode != 0, 'タイムアウトで異常終了しない'
    stderr_str = stderr.decode('utf-8', errors='ignore')
    assert 'タイムアウト' in stderr_str or 'ERROR' in stderr_str, 'タイムアウトエラーが出力されない'
    assert 2.5 < elapsed < 4.5, f'3秒付近で終了しない: {elapsed}'

def test_max_processing_time_invalid():
    """
    .envのMAX_PROCESSING_TIMEに不正値や空文字を設定した場合、config.pyのデフォルト値(600)が使われるか確認
    """
    for val in ['abc', '']:
        set_env_value('MAX_PROCESSING_TIME', val)
        config = load_config()
        assert config['MAX_PROCESSING_TIME'] == 10, f'不正値({val})でデフォルト値10が使われない'

def teardown_module(module):
    # テスト後にMAX_PROCESSING_TIMEを1に戻す
    set_env_value('MAX_PROCESSING_TIME', '1')
