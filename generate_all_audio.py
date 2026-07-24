"""批量为所有句型的例句生成 Edge TTS 语音"""
import sys, json, os, asyncio, hashlib
sys.stdout.reconfigure(encoding='utf-8')
import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "-10%"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def sent_id(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()[:10]

async def gen(text, path):
    c = edge_tts.Communicate(text.strip(), VOICE, rate=RATE)
    await c.save(path)

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # 收集所有不重复的英文句子
    sentences = set()
    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.startswith('pattern_') or not fname.endswith('.json'):
            continue
        if 'index' in fname or 'all_' in fname:
            continue
        with open(os.path.join(DATA_DIR, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
        for ex in data.get('examples', []):
            if ex.get('en'): sentences.add(ex['en'].strip())
        for v in data.get('variations', []):
            if v.get('en'): sentences.add(v['en'].strip())

    # 加载已有映射
    map_path = os.path.join(AUDIO_DIR, "audio_map.json")
    if os.path.exists(map_path):
        with open(map_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    else:
        mapping = {}

    print(f"共 {len(sentences)} 条不重复句子")

    new_count = 0
    skip_count = 0
    for i, sent in enumerate(sorted(sentences), 1):
        sid = sent_id(sent)
        filename = f"{sid}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        mapping[sent] = filename

        if os.path.exists(filepath):
            skip_count += 1
            continue

        print(f"  [{i}] {sent[:60]}")
        try:
            await gen(sent, filepath)
            new_count += 1
        except Exception as e:
            print(f"       FAIL: {e}")

    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {new_count} new, {skip_count} skipped, {len(mapping)} total")

if __name__ == "__main__":
    asyncio.run(main())
