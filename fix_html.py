"""Replace inline data in index.html with dynamic loading from data.js"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '// ===================== 索引 ====================='
end_marker = '// ===================== 练习模式定义 ====================='

start = content.find(start_marker)
end = content.find(end_marker)
if start == -1 or end == -1:
    print(f'ERROR: markers not found start={start} end={end}')
    sys.exit(1)

print(f'Block: {start}-{end} ({end-start} chars)')

new_block = (
    "// ===================== 从 data.js 动态生成 =====================\n"
    "var PATTERN_INDEX = [];\n"
    "var PATTERNS_BY_ID = ALL_PATTERNS;\n"
    "Object.keys(PATTERNS_BY_ID).forEach(function(k) {\n"
    "  var p = PATTERNS_BY_ID[k];\n"
    "  PATTERN_INDEX.push({unit: p.unit, id: p.id, title: p.title, available: false});\n"
    "});\n"
    "PATTERN_INDEX.sort(function(a,b){ return a.id - b.id; });\n"
    "if (PATTERN_INDEX.length > 0) PATTERN_INDEX[0].available = true;\n"
    "\n"
    "var UNITS = [\n"
    '  {num:1,name:"第一单元：入门的12种句型",icon:"\U0001F331"},\n'
    '  {num:2,name:"第二单元：生活必用的14种句型",icon:"\U0001F3E0"},\n'
    '  {num:3,name:"第三单元：畅快聊天12种句型",icon:"\U0001F4AC"},\n'
    '  {num:4,name:"第四单元：无障碍沟通12种句型",icon:"\U0001F680"}\n'
    "];\n\n"
)

content = content[:start] + new_block + content[end:]

# Replace all LOADED_PATTERNS references
content = content.replace('LOADED_PATTERNS[id]', 'PATTERNS_BY_ID[id]')
content = content.replace('LOADED_PATTERNS[currentPatternId]', 'PATTERNS_BY_ID[currentPatternId]')
content = content.replace('Object.values(LOADED_PATTERNS)', 'Object.values(PATTERNS_BY_ID)')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done - replaced inline data with dynamic loading')
