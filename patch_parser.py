import re

FILE_PATH = r"parser\structure_parser.py"
with open(FILE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Make nonlocal variables accessible
text = re.sub(
    r'def add_text\(text: str, page: int, has_inline_math: bool = False\):',
    r'def add_text(text: str, page: int, has_inline_math: bool = False):\n            nonlocal current_chapter, current_section, current_clause',
    text, count=1
)

# Replace the text-dropping logic
old_logic = """            if not text or not current_clause:
                return"""

new_logic = """            if not text:
                return
            if not current_clause:
                # Rescue orphaned text
                if not current_chapter:
                    current_chapter = Chapter(id="CH-FRONT-0", number="FRONT-0", title="Preamble / Front Matter", page_span=[page])
                    chapters.append(current_chapter)
                if not current_section:
                    current_section = self._make_section("Preface", "Document Preface", page, current_chapter)
                current_clause = self._make_clause("", "Orphaned Content", page, current_section)"""

text = text.replace(old_logic, new_logic)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("Patcher executed!")
