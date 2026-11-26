"""script.json から ボイロ用の台本と字幕用テキストを書き出す (Manim 不要)

    python export_text.py
      -> out/voice_葵.txt, out/voice_茜.txt : 話者ごとの読み (ファイル名 kaisetsu-XX に対応する番号付き)
      -> out/dialogue.txt                  : 掛け合い全体 (話者：セリフ)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
out = HERE / "out"
out.mkdir(exist_ok=True)

segs = cfg["segments"]
by = {}
for s in segs:
    by.setdefault(s.get("speaker", ""), []).append(f'{s["id"]}\t{s["text"]}')
for spk, lines in by.items():
    (out / f"voice_{spk}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(out / "dialogue.txt").write_text(
    "\n".join(f'{s.get("speaker", "")}：{s.get("sub", s["text"])}' for s in segs) + "\n", encoding="utf-8")
print(f"{len(segs)} 駒を書き出しました -> {out}")
