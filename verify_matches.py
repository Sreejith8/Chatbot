import re

with open('doc/chatbotPresentation.tex', 'r') as f:
    pres = f.read()

with open('doc/finalReport.tex', 'r') as f:
    rep = f.read()

# Let's extract some significant text chunks from presentation and search them in the report
# We will ignore common presentation commands like \item, \textbf, etc.

def clean_text(t):
    t = re.sub(r'\\[a-zA-Z]+\{?[^}]*\}?', '', t)
    t = re.sub(r'[^a-zA-Z0-9 ]', '', t)
    return ' '.join(t.split()).lower()

pres_chunks = re.split(r'\\begin\{frame\}|\\end\{frame\}', pres)
missing = []

rep_clean = clean_text(rep)

for chunk in pres_chunks:
    if len(chunk) < 100: continue
    
    # Extract bullet points 
    items = re.findall(r'\\item(.*?)(?=\\item|\\end|\Z)', chunk, re.DOTALL)
    for item in items:
        item_clean = clean_text(item)
        if len(item_clean) > 50 and item_clean not in rep_clean:
            # Let's verify by just substrings since clean_text might strip too much
            parts = [p for p in item_clean.split() if len(p) > 3]
            if len(parts) > 5:
                # check if a sequence of 5 words is in the report
                seq = ' '.join(parts[:5])
                if seq not in rep_clean:
                    missing.append(item.strip())

print(f"Found {len(missing)} potentially unmatched long items from Presentation.")
for i in missing[:5]:
    print("-", i[:100], "...")
