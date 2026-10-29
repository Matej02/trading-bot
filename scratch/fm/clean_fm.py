"""Zhusteny korpus FM: pro kazdou slozku autora/modulu jeden soubor v scratch/fm/korpus.
- orezani odsazeni a prazdnych radku
- radky opakujici se na vetsine stran souboru (zahlavi sablony) jen jednou
- stranky jen s 'OTÁZKY'/'POZNÁMKY' a nadpisem pryc
- u kazde strany pocet obrazku (pymupdf), at vim, kde jsou grafy"""
import collections
import os
import re

import pymupdf

SRC = r"D:\youtube\FM pdfka"
TXT = r"D:\Trading bot\scratch\fm\txt"
OUT = r"D:\Trading bot\scratch\fm\korpus"
os.makedirs(OUT, exist_ok=True)

groups = collections.defaultdict(list)
for root, _, files in os.walk(TXT):
    for f in sorted(files):
        rel = os.path.relpath(os.path.join(root, f), TXT)
        parts = rel.split(os.sep)
        groups["__".join(parts[:2])].append(rel)

sizes = {}
for g, rels in sorted(groups.items()):
    out = []
    for rel in sorted(rels, key=lambda r: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", r)]):
        raw = open(os.path.join(TXT, rel), encoding="utf-8", errors="replace").read()
        pages = [[ln.strip() for ln in p.splitlines() if ln.strip()] for p in raw.split("\f")]
        pages = [p for p in pages if p]
        cnt = collections.Counter(ln for p in pages for ln in set(p))
        rep = {ln for ln, c in cnt.items() if len(pages) >= 4 and c >= 0.5 * len(pages)}
        try:
            doc = pymupdf.open(os.path.join(SRC, rel[:-4] + ".pdf"))
            imgs = [len(pg.get_images()) for pg in doc]
        except Exception:
            imgs = []
        out.append(f"\n##### {rel[:-4]}  ({len(pages)} str., obrázky na str.: {imgs})")
        seen = set()
        for i, p in enumerate(pages, 1):
            body = []
            for ln in p:
                if ln in rep:
                    if ln in seen:
                        continue
                    seen.add(ln)
                body.append(re.sub(r"\s{2,}", "  ", ln))
            core = [b for b in body if b not in rep]
            if core and set(x.upper() for x in core) <= {"OTÁZKY", "POZNÁMKY"}:
                continue
            if core and core[0].upper() == "POZNÁMKY" and len(core) <= 2:
                continue
            out.append(f"[s{i}] " + " | ".join(body))
    txt = "\n".join(out)
    open(os.path.join(OUT, g + ".txt"), "w", encoding="utf-8").write(txt)
    sizes[g] = len(txt)
for g, s in sizes.items():
    print(f"{s:8d}  {g}")
print("celkem", sum(sizes.values()))
