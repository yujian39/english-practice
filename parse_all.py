"""批量解析全部句型 → JSON + 自动生成中文翻译和关键词"""
import sys, json, re, os
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

DOCX_PATH = r"C:\Users\16152\Desktop\50个句型搞定口语.docx"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def is_en(text):
    t = text.strip()
    if not t or len(t) < 3: return False
    zh = len(re.findall(r'[\u4e00-\u9fff]', t))
    if zh > 3: return False
    return bool(re.search(r'[a-zA-Z]{2,}', t))

def is_var_label(t):
    return bool(re.match(r'^一般(现在|过去|将来)时(肯定|否定)型', t.strip()))

def is_pattern_title(t):
    m = re.match(r'^(\d+)\.\s+(.+)', t.strip())
    if not m: return False, 0, ''
    num = int(m.group(1))
    title = m.group(2).strip()
    if len(title) >= 80: return False, 0, ''
    has_sig = any(c in title for c in '...+?？')
    has_sig = has_sig or '...' in title or '\u2026' in title
    if not has_sig and num > 20: return False, 0, ''
    return True, num, title

# ---- 中文翻译模板 ----
def gen_zh(label, en):
    """根据时态标签和英文句子生成中文翻译"""
    e = en.lower().strip().rstrip('.')

    # 时态前缀
    if '过去' in label:
        prefix = '（曾经）'
    elif '将来' in label:
        prefix = '将会'
    else:
        prefix = ''

    # 否定
    neg = '否定' in label

    # 从英文提取核心信息
    # There be 句型
    m = re.match(r"there (is|are|was|were|will be|isn't|aren't|wasn't|weren't|won't be) (.+)", e)
    if m:
        verb = m.group(1)
        rest = m.group(2)
        if neg:
            return f'{prefix}没有{translate_rest(rest)}'
        else:
            return f'{prefix}有{translate_rest(rest)}'

    # 主语+感官动词
    m = re.match(r"(she|he|it|they|you|we|i) (look|sound|feel|taste|smell)s? (like )?(.+)", e)
    if m:
        subj = translate_subj(m.group(1))
        verb = translate_sense(m.group(2))
        obj = m.group(4).strip()
        return f'{subj}{verb}像{translate_rest(obj)}'

    # 通用：返回英文原文作为 fallback
    return en

def translate_rest(s):
    """翻译 There be 后面的部分"""
    s = s.strip().rstrip('.')
    # 常见名词
    words = {
        'a girl': '一个女孩', 'two girls': '两个女孩',
        'a boy': '一个男孩', 'two boys': '两个男孩',
        'a pen': '一支笔', 'a book': '一本书',
        'two books': '两本书', 'a cat': '一只猫',
        'a dog': '一条狗', 'a man': '一个男人',
        'an old man': '一位老人', 'a woman': '一个女人',
        'a car': '一辆车', 'a house': '一栋房子',
        'a tree': '一棵树', 'some water': '一些水',
        'a pen and two books on the desk': '桌子上一支笔和两本书',
        'many people': '很多人', 'some students': '一些学生',
    }
    for k, v in words.items():
        if k in s:
            return v
    return s

def translate_subj(s):
    return {'i':'我','you':'你','he':'他','she':'她','it':'它','we':'我们','they':'他们'}.get(s,s)

def translate_sense(s):
    return {'look':'看','sound':'听','feel':'感觉','taste':'尝','smell':'闻'}.get(s,s)

# ---- 关键词提取 ----
def extract_key(label, en):
    """从英文句子中提取适合填空的关键词"""
    e = en.strip()
    # There be 句型：提取 be 动词（含 not）
    m = re.match(r"There ([a-zA-Z']+n?'t|[a-zA-Z']+ be|[a-zA-Z']+)\s", e, re.I)
    if m:
        return m.group(1).lower()
    # 感官动词
    m = re.match(r".+? (look|sound|feel|taste|smell)s?", e, re.I)
    if m: return m.group(1).lower()
    # 通用：取第二个词（通常是动词）
    parts = e.split()
    if len(parts) >= 2:
        return parts[1].lower().rstrip('.,;:')
    return parts[0].lower() if parts else ''

# ===================== 主解析 =====================
def parse_all():
    doc = Document(DOCX_PATH)
    texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # 找所有句型标题位置
    starts = []
    for i, t in enumerate(texts):
        ok, num, title = is_pattern_title(t)
        if ok:
            starts.append((i, num, title))

    # 按单元分组（根据在文档中的顺序）
    unit_boundaries = []
    current_unit = 0
    for idx, (para_i, num, title) in enumerate(starts):
        if num == 1 and idx > 0:
            current_unit += 1
        unit_boundaries.append(current_unit)

    patterns = []
    for idx, (para_i, num, title) in enumerate(starts):
        unit = unit_boundaries[idx] + 1
        end_i = starts[idx+1][0] if idx+1 < len(starts) else len(texts)
        chunk = texts[para_i:end_i]

        # 提取讲解
        explanation = ''
        if len(chunk) > 1 and not is_en(chunk[1]) and not is_var_label(chunk[1]):
            explanation = chunk[1]

        # 提取例句和讲解
        examples = []
        current_note = ''
        in_var = False
        for t in chunk[2:]:
            if '真的学得会' in t:
                in_var = True
                break
            if re.match(r'^（\d+）', t):
                current_note = re.sub(r'^（\d+）\s*', '', t).strip()
                continue
            if is_en(t):
                examples.append({'en': t.strip(), 'note': current_note})
                current_note = ''

        # 提取时态变化
        variations = []
        if in_var:
            cur_label = ''
            for t in chunk:
                if '真的学得会' in t:
                    # 从这之后开始
                    idx2 = chunk.index(t)
                    for vt in chunk[idx2+1:]:
                        if is_var_label(vt):
                            cur_label = vt.strip()
                        elif is_en(vt) and cur_label:
                            en = vt.strip()
                            variations.append({
                                'label': cur_label,
                                'en': en,
                                'zh': gen_zh(cur_label, en),
                                'key': extract_key(cur_label, en)
                            })
                    break

        pid = len(patterns) + 1
        patterns.append({
            'id': pid,
            'unit': unit,
            'num_in_unit': num,
            'title': title,
            'explanation': explanation,
            'examples': examples,
            'variations': variations
        })

    return patterns

if __name__ == '__main__':
    patterns = parse_all()
    os.makedirs(OUT_DIR, exist_ok=True)

    # 保存单个文件
    for p in patterns:
        path = os.path.join(OUT_DIR, f'pattern_{p["id"]:02d}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(p, f, ensure_ascii=False, indent=2)

    # 保存汇总
    summary = {p['id']: p for p in patterns}
    with open(os.path.join(OUT_DIR, 'all_patterns.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False)

    print(f'共解析 {len(patterns)} 个句型')
    for p in patterns:
        ex = len(p['examples'])
        va = len(p['variations'])
        print(f'  [{p["id"]:2d}] U{p["unit"]} {p["title"][:40]:40s} 例句:{ex} 变化:{va}')
