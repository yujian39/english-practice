"""将所有句型数据和音频映射合并，生成可嵌入 HTML 的 JS 数据"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")

# 读取所有句型
patterns = {}
for fname in sorted(os.listdir(DATA_DIR)):
    if not fname.startswith('pattern_') or not fname.endswith('.json'):
        continue
    if 'index' in fname or 'all_' in fname:
        continue
    with open(os.path.join(DATA_DIR, fname), 'r', encoding='utf-8') as f:
        data = json.load(f)
    pid = data['id']
    patterns[pid] = data

# 读取音频映射
with open(os.path.join(AUDIO_DIR, 'audio_map.json'), 'r', encoding='utf-8') as f:
    audio_map = json.load(f)

# 生成 JS
js_lines = []
js_lines.append("// 自动生成 - 请勿手动编辑")
js_lines.append("var ALL_PATTERNS = " + json.dumps(patterns, ensure_ascii=False) + ";")
js_lines.append("")
js_lines.append("var AUDIO_MAP = " + json.dumps(audio_map, ensure_ascii=False) + ";")

js_text = "\n".join(js_lines)

# 写入文件
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(js_text)

print(f"Generated data.js: {len(patterns)} patterns, {len(audio_map)} audio entries")
print(f"File size: {os.path.getsize(out_path) / 1024:.0f} KB")
