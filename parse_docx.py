"""解析 50个句型搞定口语.docx → 结构化 JSON（当前只提取句型1作为模板验证）"""
import sys, json, re, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document

DOCX_PATH = r"C:\Users\16152\Desktop\50个句型搞定口语.docx"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

def is_english_sentence(text):
    """判断是否是纯英文例句（非中文讲解）"""
    t = text.strip()
    if not t:
        return False
    # 包含大量中文 → 不是例句
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', t))
    if chinese_chars > 2:
        return False
    # 必须含英文字母
    if not re.search(r'[a-zA-Z]{2,}', t):
        return False
    # 排除标题性质的行（如 "1. There be..." 或 "真的学得会！"）
    if re.match(r'^\d+\.\s', t):
        return False
    if '学得会' in t or '句型' in t and '各种' in t:
        return False
    return True

def is_variation_label(text):
    """判断是否是时态变化的标签行，如 '一般现在时肯定型（主语为单数）'"""
    t = text.strip()
    return bool(re.match(r'^一般(现在|过去|将来)时(肯定|否定)型', t))

def parse_pattern_1(paragraphs):
    """解析第一个句型的数据"""
    # 段落索引：0=标题, 1=总讲解, 2-12=讲解+例句, 13=变化标题, 14+=时态变化
    title_text = paragraphs[0].strip()
    # 提取编号和标题
    match = re.match(r'(\d+)\.\s*(.*)', title_text)
    pattern_num = int(match.group(1))
    pattern_title = match.group(2).strip()

    # 总讲解
    explanation = paragraphs[1].strip()

    # 提取讲解部分的例句和对应讲解
    examples = []
    current_explanation = ""
    in_variation_section = False

    for i in range(2, len(paragraphs)):
        text = paragraphs[i].strip()

        # 进入时态变化区域
        if '真的学得会' in text:
            in_variation_section = True
            continue
        if in_variation_section:
            break

        # 讲解段落（以（数字）开头，或纯中文）
        if re.match(r'^（\d+）', text):
            # 去掉编号前缀，作为讲解
            current_explanation = re.sub(r'^（\d+）\s*', '', text).strip()
            continue

        # 纯英文例句
        if is_english_sentence(text):
            examples.append({
                "en": text.strip(),
                "note": current_explanation if current_explanation else ""
            })
            current_explanation = ""  # 用完清空

    # 提取时态变化
    variations = []
    current_label = ""
    for i in range(2, len(paragraphs)):
        text = paragraphs[i].strip()
        if '真的学得会' in text:
            # 从这之后开始提取变化
            for j in range(i + 1, len(paragraphs)):
                vtext = paragraphs[j].strip()
                if is_variation_label(vtext):
                    current_label = vtext
                elif is_english_sentence(vtext) and current_label:
                    variations.append({
                        "label": current_label,
                        "en": vtext.strip()
                    })
            break

    return {
        "id": pattern_num,
        "title": pattern_title,
        "explanation": explanation,
        "examples": examples,
        "variations": variations
    }


def main():
    doc = Document(DOCX_PATH)
    all_texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # 找到句型1的范围（从 "1. There be" 到 "2. 主语+sound..." 之前）
    start = None
    end = None
    for i, t in enumerate(all_texts):
        if t.startswith('1. There be'):
            start = i
        elif t.startswith('2. 主语+sound') and start is not None:
            end = i
            break

    if start is None or end is None:
        print("ERROR: 找不到句型1的范围")
        return

    pattern = parse_pattern_1(all_texts[start:end])
    print(json.dumps(pattern, ensure_ascii=False, indent=2))

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "pattern_01.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pattern, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存到 {output_path}")
    print(f"   讲解例句: {len(pattern['examples'])} 条")
    print(f"   时态变化: {len(pattern['variations'])} 条")


if __name__ == "__main__":
    main()
