# part0: 角運動量保存則 の解説アニメーション

Make-RW-memo の `part0/台本.txt` の「説明入れる」に入る、琴葉姉妹の掛け合いパート (23駒)。

## ファイル
| ファイル | 中身 |
|---|---|
| `script.json` | 駒ごとの話者・セリフ (`text` = ボイロの読み, `sub` = 字幕用)・尺 |
| `main.py` | アニメーション本体 (シーン名 `Part0`) |
| `export_text.py` | ボイロ用台本・掛け合いテキストの書き出し |
| `out/subtitles.srt` | 全体字幕 (`葵：…` 形式) ※レンダリング時に生成 |
| `out/subtitles_葵.srt`, `out/subtitles_茜.srt` | 話者別字幕 (キャラごとに字幕スタイルを分ける用) |
| `out/timing.csv` | 駒ごとの話者・開始・終了秒 |

動画 (`media/`) は git 管理外。各自レンダリングする。

## 作業の流れ
1. `script.json` のセリフを直す
2. `python export_text.py` → `out/voice_葵.txt` / `out/voice_茜.txt` をボイロに流す
3. 音声を Make-RW-memo 側に置く:
   `Make-RW-memo/part0/素材/琴葉姉妹音声/<葵|茜>/kaisetsu-<番号>.wav` (例: `茜/kaisetsu-05.wav`)
   - 場所と名前は `script.json` の `voice_dir` / `voice_file` で変更可
   - Animations と Make-RW-memo が同じフォルダに並んでいる前提
4. レンダリング → 各駒の尺が「音声の長さ + 0.4秒」に合い、字幕も作り直される
   (音声が無い駒は文字数から推定。`duration` に秒数を書けば固定)
   - アニメーションの方が長い駒は、アニメーションの長さが優先される
5. 編集ソフトで `sections/` の駒クリップと音声を頭揃えで並べる

`embed_voice: true` にすると音声入りで書き出す (確認用)。

## レンダリング
```powershell
python -m manim -qh --save_sections main.py Part0
```
- 出力: `media/videos/main/1080p60/Part0.mp4` (全編), `media/videos/main/1080p60/sections/Part0_XXXX_segYY.mp4` (駒ごと)
- 確認用の低画質は `-qh` → `-ql`
- 必要なもの: Python 3.10〜3.12 + `pip install manim`, LaTeX (TeX Live), フォント Noto Sans JP

### Windows の注意
パスが長い (OneDrive 配下など) と `DLL load failed ... ファイル名または拡張子が長すぎます` で落ちることがある。
その場合は短いドライブ名を割り当ててから実行する:
```powershell
subst P: "<このフォルダのパス>"
cd P:\
python -m manim -qh --save_sections main.py Part0
```
