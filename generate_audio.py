"""为 JSON 数据中的英文例句生成 mp3 语音文件（Edge TTS）"""
import sys, json, os, asyncio, hashlib
sys.stdout.reconfigure(encoding='utf-8')

import edge_tts

VOICE = "en-US-JennyNeural"  # 自然的美式女声
RATE = "-10%"                # 稍微放慢，适合学习
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

def sentence_id(text):
    """用句子内容生成短ID，作为文件名"""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()[:10]

async def generate_one(text, output_path):
    """生成单条语音"""
    communicate = edge_tts.Communicate(text.strip(), VOICE, rate=RATE)
    await communicate.save(output_path)

async def main():
    json_path = os.path.join(os.path.dirname(__file__), "data", "pattern_01.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 收集所有不重复的英文句子
    sentences = set()
    for ex in data["examples"]:
        sentences.add(ex["en"].strip())
    for v in data["variations"]:
        sentences.add(v["en"].strip())

    os.makedirs(AUDIO_DIR, exist_ok=True)

    print(f"共 {len(sentences)} 条不重复句子，开始生成语音...\n")

    for i, sent in enumerate(sorted(sentences), 1):
        sid = sentence_id(sent)
        filename = f"{sid}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        if os.path.exists(filepath):
            print(f"  [{i}] 已存在，跳过: {sent}")
            continue

        print(f"  [{i}] 生成中: {sent}")
        try:
            await generate_one(sent, filepath)
            print(f"       → {filename}")
        except Exception as e:
            print(f"       ❌ 失败: {e}")

    # 输出句子→文件名映射，供网页使用
    mapping = {}
    for sent in sentences:
        mapping[sent.strip()] = f"{sentence_id(sent)}.mp3"

    mapping_path = os.path.join(AUDIO_DIR, "audio_map.json")
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 映射表已保存到 {mapping_path}")

if __name__ == "__main__":
    asyncio.run(main())
