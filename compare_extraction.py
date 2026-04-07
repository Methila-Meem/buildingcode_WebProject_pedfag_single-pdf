import json
import re
import os

RAW_PATH = r"storage\raw_bcbc_2024_web_version_revision2.json"
STRUCT_PATH = r"storage\output\structured_document.json"

def strip_html(html_str):
    if not html_str: return ""
    return re.sub(r'<[^>]+>', ' ', html_str)

def get_raw_text_length():
    with open(RAW_PATH, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    text_chunks = []
    if 'pages' in raw_data:
        for page in raw_data['pages']:
            for child in page.get('children', []):
                if 'html' in child:
                    text_chunks.append(strip_html(child['html']))
    return len(" ".join(text_chunks).split())

def get_structured_text_length():
    with open(STRUCT_PATH, 'r', encoding='utf-8') as f:
        struct_data = json.load(f)
        
    text_chunks = []
    for ch in struct_data.get('chapters', []):
        text_chunks.append(ch.get('title', ''))
        for sec in ch.get('sections', []):
            text_chunks.append(sec.get('title', ''))
            for cl in sec.get('clauses', []):
                for item in cl.get('content', []):
                    if item.get('type') in ['text', 'sub_clause']:
                        text_chunks.append(item.get('value', ''))
                for tab in cl.get('tables', []):
                    text_chunks.append(tab.get('caption', ''))
                for fig in cl.get('figures', []):
                    text_chunks.append(fig.get('caption', ''))
    return len(" ".join(text_chunks).split())

if not os.path.exists(RAW_PATH):
    print("Raw file not found!")
elif not os.path.exists(STRUCT_PATH):
    print("Structured file not found!")
else:
    raw_words = get_raw_text_length()
    struct_words = get_structured_text_length()
    
    print(f"Raw words: {raw_words}")
    print(f"Structured words: {struct_words}")
    if raw_words > 0:
        match_pct = (struct_words / raw_words) * 100
        print(f"Approximate retention rate: {match_pct:.2f}%")
