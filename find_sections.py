import re

with open('doc/chatbotPresentation.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract frame titles
titles = re.findall(r'\\frametitle\{([^}]+)\}', text)
if not titles:
    # Try \begin{frame}{Title}
    titles = re.findall(r'\\begin\{frame\}(?:\[.*?\])?\{([^}]+)\}', text)

print("Sections in Presentation:")
for t in set(titles):
    print("- " + t)
