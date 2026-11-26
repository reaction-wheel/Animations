"""
Part0 解説パート: 角運動量保存則 と リアクションホイールの原理 (琴葉姉妹の掛け合い)

使い方 (このフォルダで実行):
    python -m manim -qh --save_sections main.py Part0     (1080p60)
    python -m manim -ql --save_sections main.py Part0     (確認用の低画質)

セリフ・話者・駒の長さは script.json で編集する。
音声 (voice_dir/voice_file) があれば、その長さに合わせて各駒の尺が決まる。
書き出し後 out/ に字幕 (srt) と駒のタイミング (csv) が作られる。
"""
import json
import wave
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
SEGS = {s["id"]: s for s in CFG["segments"]}
OUT = HERE / "out"

JP = "Noto Sans JP"  # 日本語フォント (無ければ "Yu Gothic" や "Meiryo" に変更)

# 色の約束事: L=黄, I=水色, ω=赤, 機体=青, ホイール=オレンジ
C_L, C_I, C_W = YELLOW, TEAL, RED_C
C_BODY, C_WHEEL = BLUE_C, ORANGE


# ---------------------------------------------------------------- 尺の計算
def voice_path(s) -> Path:
    d = CFG.get("voice_dir", "voice").format(speaker=s.get("speaker", ""), id=s["id"])
    f = CFG.get("voice_file", "{id}.wav").format(speaker=s.get("speaker", ""), id=s["id"])
    return (HERE / d / f).resolve()


def wav_length(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def seg_duration(s) -> float:
    if s.get("duration"):
        return float(s["duration"])
    vp = voice_path(s)
    if vp.exists():
        return wav_length(vp) + float(CFG.get("pad_after_voice", 0.4))
    return len(s["text"]) / 6.5 + 0.8  # ボイロの読み上げ速度からの推定


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def jp(text, size=36, color=WHITE, **kw):
    return Text(text, font=JP, font_size=size, color=color, **kw)


# ---------------------------------------------------------------- 駒管理つき Scene
class SegmentScene(Scene):
    """seg("01") で駒を区切る。前の駒はセリフの長さまで待ってから次へ進む。"""

    def setup(self):
        self._cur = None   # 尺を待っている途中の駒
        self._open = None  # 尺は満たしたが次の駒がまだ始まっていない駒 (退場アニメ中)
        self._log = []

    def now(self):
        return self.renderer.time

    def seg(self, sid):
        self.hold()
        self._commit()
        s = SEGS[sid]
        self.next_section(f"seg{sid}")
        self._cur = (s, self.now(), seg_duration(s))
        if CFG.get("embed_voice") and voice_path(s).exists():
            self.add_sound(str(voice_path(s)))

    def hold(self):
        """セリフの長さに達するまで待つ。この後のアニメは同じ駒の末尾(セリフ後の間)になる。"""
        if not self._cur:
            return
        s, t0, dur = self._cur
        rest = dur - (self.now() - t0)
        if rest > 1 / 60:
            self.wait(rest)
        self._open = (s, t0)
        self._cur = None

    def _commit(self):
        if self._open:
            s, t0 = self._open
            self._log.append((s, t0, self.now()))
            self._open = None

    def finish(self):
        self.hold()
        self._commit()
        OUT.mkdir(exist_ok=True)
        srt_all, srt_by = [], {}
        csv = ["id,speaker,start,end,length,text"]
        for s, a, b in self._log:
            sub, spk = s.get("sub", s["text"]), s.get("speaker", "")
            block = f"{srt_time(a)} --> {srt_time(b)}\n{sub}\n"
            srt_all.append(f"{len(srt_all) + 1}\n{srt_time(a)} --> {srt_time(b)}\n{spk}：{sub}\n")
            lst = srt_by.setdefault(spk, [])
            lst.append(f"{len(lst) + 1}\n{block}")
            csv.append(f'{s["id"]},{spk},{a:.3f},{b:.3f},{b - a:.3f},"{sub}"')
        (OUT / "subtitles.srt").write_text("\n".join(srt_all), encoding="utf-8")
        for spk, lst in srt_by.items():
            (OUT / f"subtitles_{spk}.srt").write_text("\n".join(lst), encoding="utf-8")
        (OUT / "timing.csv").write_text("\n".join(csv) + "\n", encoding="utf-8-sig")


# ---------------------------------------------------------------- 部品
def spinner_factory(anchor, r, ang):
    """上から見たスケーター: 胴体 + 腕 + 手(おもり) + 顔"""

    def build():
        c = anchor.get_center()
        a, rr = ang.get_value(), r.get_value()
        d = np.array([np.cos(a), np.sin(a), 0.0])
        n = np.array([-d[1], d[0], 0.0])
        arm = Line(c - rr * d, c + rr * d, stroke_width=12, color=GREY_B)
        hands = VGroup(*[Dot(c + k * rr * d, radius=0.2, color=C_I) for k in (1, -1)])
        body = Ellipse(width=1.3, height=0.8, fill_color=BLUE_E, fill_opacity=1,
                       stroke_color=WHITE, stroke_width=3).rotate(a).move_to(c)
        head = Dot(c + 0.25 * n, radius=0.2, color=WHITE)
        return VGroup(arm, body, hands, head)

    return always_redraw(build)


def satellite():
    box = RoundedRectangle(corner_radius=0.2, width=2.6, height=2.6,
                           fill_color=C_BODY, fill_opacity=0.25, stroke_color=C_BODY, stroke_width=5)
    panels = VGroup()
    for k in (1, -1):
        p = Rectangle(width=1.3, height=0.8, fill_color=BLUE_E, fill_opacity=0.9,
                      stroke_color=BLUE_B, stroke_width=2)
        grid = VGroup(*[Line(p.get_top(), p.get_bottom(), stroke_width=1, color=BLUE_B)
                        .shift(RIGHT * x) for x in (-0.33, 0, 0.33)])
        panel = VGroup(p, grid).next_to(box, RIGHT * k, buff=0.25)
        strut = Line(box.get_edge_center(RIGHT * k), panel.get_edge_center(-RIGHT * k),
                     stroke_width=4, color=GREY_B)
        panels.add(VGroup(strut, panel))
    antenna = Triangle(fill_color=WHITE, fill_opacity=1, stroke_width=0).scale(0.18)
    antenna.next_to(box, UP, buff=0.05)
    return VGroup(panels, box, antenna)


def wheel(radius=0.85):
    rim = Circle(radius=radius, stroke_color=C_WHEEL, stroke_width=10)
    spokes = VGroup(*[Line(ORIGIN, radius * np.array([np.cos(t), np.sin(t), 0]),
                           stroke_width=5, color=C_WHEEL) for t in np.arange(0, TAU, TAU / 6)])
    hub = Dot(radius=0.1, color=WHITE)
    mark = Dot(radius * 0.7 * RIGHT, radius=0.09, color=WHITE)
    return VGroup(spokes, rim, hub, mark)


def curved_arrow(center, radius, start, angle, color, width=6):
    return CurvedArrow(center + radius * np.array([np.cos(start), np.sin(start), 0]),
                       center + radius * np.array([np.cos(start + angle), np.sin(start + angle), 0]),
                       angle=angle, color=color, stroke_width=width, tip_length=0.25)


def stars(n=90, seed=3):
    rng = np.random.default_rng(seed)
    return VGroup(*[Dot([rng.uniform(-7.1, 7.1), rng.uniform(-4, 4), 0],
                        radius=rng.uniform(0.008, 0.03), color=WHITE,
                        fill_opacity=rng.uniform(0.3, 0.9)) for _ in range(n)])


# ---------------------------------------------------------------- 本編
class Part0(SegmentScene):
    def construct(self):
        self.part_spinner()
        self.part_reaction_wheel()
        self.finish()

    # ---------- 前半: スピンと角運動量保存 ----------
    def part_spinner(self):
        # 01 葵: まずは角運動量保存則から
        self.seg("01")
        title = jp("角運動量保存則", 80, weight=BOLD)
        sub = jp("Conservation of Angular Momentum", 30, GREY_B)
        VGroup(title, sub).arrange(DOWN, buff=0.4)
        self.play(Write(title), FadeIn(sub, shift=UP * 0.2), run_time=1.5)
        self.hold()
        self.play(FadeOut(VGroup(title, sub)), run_time=0.5)

        # スピンの物理: L = I ω 一定, I(r) = I0 + 2 m r^2
        I0, m = 0.4, 1.0
        I_of = lambda rr: I0 + 2 * m * rr ** 2
        r = ValueTracker(2.0)
        ang = ValueTracker(0.0)
        L = I_of(2.0) * 1.0  # 腕を伸ばした状態で ω = 1 rad/s
        omega = lambda: L / I_of(r.get_value())
        ang.add_updater(lambda t, dt: t.increment_value(omega() * dt))
        anchor = Dot(ORIGIN, radius=0, fill_opacity=0)
        sp = spinner_factory(anchor, r, ang)

        # 02 葵: スピンで腕を縮めると速くなる
        self.seg("02")
        caption = jp("フィギュアスケートのスピン(上から見た図)", 30, GREY_B).to_edge(UP)
        self.add(ang, anchor)
        self.play(FadeIn(sp), FadeIn(caption))
        self.wait(1.5)
        self.play(r.animate.set_value(0.7), run_time=2.5, rate_func=smooth)

        # 03 茜: あー、あれな
        self.seg("03")
        self.play(r.animate.set_value(2.0), run_time=1.5, rate_func=smooth)

        # 04 葵: 外からは誰も押していない
        self.seg("04")
        self.play(anchor.animate.move_to(LEFT * 3.6 + DOWN * 0.3), FadeOut(caption), run_time=1.5)
        q = jp("外からは誰も押していない", 34).move_to(RIGHT * 3.3 + UP * 1.0)
        self.play(FadeIn(q, shift=UP * 0.2))

        # 05 茜: ほな何で速なるん？
        self.seg("05")
        why = jp("なのに速くなる…？", 34, C_L).next_to(q, DOWN, buff=0.4)
        self.play(FadeIn(why, shift=UP * 0.2), run_time=0.6)

        # 06 葵: 角運動量 L = Iω
        self.seg("06")
        key = jp("角運動量", 60, C_L, weight=BOLD).move_to(RIGHT * 3.3)
        self.play(FadeOut(VGroup(q, why)), Write(key), run_time=1.0)
        self.wait(0.8)
        eq = MathTex("L", "=", "I", "\\omega", font_size=110)
        eq[0].set_color(C_L); eq[2].set_color(C_I); eq[3].set_color(C_W)
        eq.move_to(RIGHT * 3.3 + UP * 0.6)
        lab_L = jp("角運動量 = 回転の勢い", 30, C_L).next_to(eq, UP, buff=0.5)
        self.play(ReplacementTransform(key, lab_L), Write(eq), run_time=1.4)

        # 07 葵: ω と I の意味
        self.seg("07")
        lw = jp("角速度\n(回る速さ)", 26, C_W).move_to(RIGHT * 4.9 + DOWN * 1.4)
        li = jp("慣性モーメント\n(回しにくさ)", 26, C_I).move_to(RIGHT * 2.0 + DOWN * 1.4)
        aw = Arrow(lw.get_top(), eq[3].get_bottom(), buff=0.1, color=C_W)
        ai = Arrow(li.get_top(), eq[2].get_bottom(), buff=0.1, color=C_I)
        self.play(GrowArrow(aw), FadeIn(lw, shift=UP * 0.2))
        self.wait(2.0)
        self.play(GrowArrow(ai), FadeIn(li, shift=UP * 0.2))

        # 08 茜: 回しにくさ？
        self.seg("08")
        self.play(Indicate(li, color=C_I, scale_factor=1.15), Indicate(eq[2], color=C_I), run_time=1.0)

        # 09 葵: 中心から遠いほど I が大きい
        self.seg("09")
        self.play(FadeOut(VGroup(lw, li, aw, ai, lab_L)),
                  eq.animate.scale(0.6).move_to(RIGHT * 3.3 + UP * 2.6))
        ieq = MathTex("I", "=", "\\sum", "m", "r^2", font_size=64).next_to(eq, DOWN, buff=0.4)
        ieq[0].set_color(C_I); ieq[4].set_color(C_I)
        self.play(Write(ieq))
        demos = VGroup()
        for rr, txt in ((0.45, "I 小"), (1.25, "I 大")):
            ax = Dot(radius=0.07, color=WHITE)
            orbit = DashedVMobject(Circle(radius=rr, color=GREY_B, stroke_width=2), num_dashes=24)
            rod = Line(ORIGIN, RIGHT * rr, color=GREY_B, stroke_width=4)
            ball = Dot(RIGHT * rr, radius=0.16, color=C_I)
            rl = MathTex("r", font_size=34).next_to(rod, UP, buff=0.05)
            lab = jp(txt, 30, C_I).shift(DOWN * 1.65)
            demos.add(VGroup(orbit, rod, ball, ax, rl, lab))
        demos.arrange(RIGHT, buff=0.8, aligned_edge=DOWN).move_to(RIGHT * 3.3 + DOWN * 1.4)
        self.play(LaggedStart(*[FadeIn(d, shift=UP * 0.2) for d in demos], lag_ratio=0.5), run_time=1.6)

        # 10 葵: 角運動量保存則
        self.seg("10")
        self.play(FadeOut(VGroup(demos, ieq)), eq.animate.scale(1 / 0.6).move_to(RIGHT * 3.3 + UP * 2.6))
        lab_c = jp("外からのトルクがなければ", 26, GREY_B)
        cond = MathTex("\\tau_{\\text{ext}} = 0", font_size=60)
        arrow = MathTex("\\Downarrow", font_size=50)
        res = MathTex("L", "=", "\\text{const.}", font_size=60)
        res[0].set_color(C_L)
        name = jp("角運動量保存則", 40, C_L, weight=BOLD)
        VGroup(lab_c, cond, arrow, res, name).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.3 + DOWN * 1.0)
        name.shift(DOWN * 0.2)
        self.play(FadeIn(lab_c), Write(cond))
        self.wait(0.8)
        self.play(FadeIn(arrow), Write(res))
        self.wait(1.0)
        box = SurroundingRectangle(VGroup(lab_c, cond, res, arrow, name), color=C_L, buff=0.3)
        self.play(Write(name), Create(box), run_time=1.4)

        # 11 茜: つまりどういうことや？
        self.seg("11")
        self.play(Wiggle(VGroup(box, lab_c, cond, arrow, res, name), scale_value=1.05), run_time=1.0)

        # 12 葵: I↓ → ω↑ をバーで可視化
        self.seg("12")
        self.play(FadeOut(VGroup(lab_c, cond, arrow, res, name, box)), run_time=0.6)
        base_y, bar_w = -2.4, 0.7
        k_I, k_w = 3.4 / I_of(2.0), 3.4 / (L / I_of(0.7))

        def bars():
            vals = [(I_of(r.get_value()) * k_I, C_I, 1.9), (omega() * k_w, C_W, 3.3), (1.9, C_L, 4.7)]
            return VGroup(*[Rectangle(width=bar_w, height=max(h, 0.02), fill_color=c, fill_opacity=0.85,
                                      stroke_width=0).move_to([x, base_y, 0], aligned_edge=DOWN)
                            for h, c, x in vals])

        bar_g = always_redraw(bars)
        bar_labels = VGroup(*[MathTex(t, font_size=50, color=c).move_to([x, base_y - 0.45, 0])
                              for t, c, x in (("I", C_I, 1.9), ("\\omega", C_W, 3.3), ("L", C_L, 4.7))])
        axis = Line([1.2, base_y, 0], [5.4, base_y, 0], color=GREY_B)
        const = jp("一定", 26, C_L).move_to([4.7, base_y + 2.3, 0])
        self.play(eq.animate.scale(0.8).move_to(RIGHT * 3.3 + UP * 2.9),
                  FadeIn(VGroup(bar_g, bar_labels, axis, const)))
        self.wait(1.0)
        self.play(r.animate.set_value(0.7), run_time=3, rate_func=smooth)

        # 13 茜: L を一定にするために勝手に速くなる
        self.seg("13")
        self.play(r.animate.set_value(2.0), run_time=1.5, rate_func=smooth)
        self.play(r.animate.set_value(0.7), run_time=1.5, rate_func=smooth)
        self.hold()

        ang.clear_updaters()
        bar_g.clear_updaters()
        sp.clear_updaters()
        self.play(FadeOut(VGroup(sp, bar_g, bar_labels, axis, const, eq)), run_time=0.6)
        self.remove(ang, anchor)

    # ---------- 後半: リアクションホイール ----------
    def part_reaction_wheel(self):
        C = LEFT * 3.2 + DOWN * 0.2
        Iw_over_Ib = 0.1  # ホイール/機体 の慣性モーメント比

        # 14 葵: 機体とホイール登場
        self.seg("14")
        sky = stars()
        sat = satellite().move_to(C)
        wh = wheel().move_to(C)
        title = jp("リアクションホイール", 40, C_WHEEL, weight=BOLD).to_edge(UP).shift(RIGHT * 3.3)
        self.play(FadeIn(sky), FadeIn(title, shift=DOWN * 0.2))
        self.play(FadeIn(sat, scale=0.8), run_time=1.2)
        self.wait(1.0)
        self.play(Create(wh), run_time=1.2)
        lab_b = jp("機体", 30, C_BODY).move_to(C + UP * 2.4 + RIGHT * 1.9)
        lab_w = jp("ホイール", 30, C_WHEEL).move_to(C + DOWN * 2.4 + RIGHT * 1.9)
        ar_b = Arrow(lab_b.get_left(), C + UP * 1.3 + RIGHT * 1.0, buff=0.1, color=C_BODY, stroke_width=4)
        ar_w = Arrow(lab_w.get_left(), C + DOWN * 0.6 + RIGHT * 0.6, buff=0.1, color=C_WHEEL, stroke_width=4)
        self.play(GrowArrow(ar_b), FadeIn(lab_b), GrowArrow(ar_w), FadeIn(lab_w))

        # 15 葵: 最初は L = 0
        self.seg("15")
        L0 = MathTex("L_{\\text{total}}", "=", "0", font_size=72).move_to(RIGHT * 3.3 + UP * 1.6)
        L0[0].set_color(C_L)
        still = jp("機体もホイールも静止", 28, GREY_B).next_to(L0, DOWN, buff=0.4)
        self.play(FadeOut(VGroup(lab_b, lab_w, ar_b, ar_w)), Write(L0), FadeIn(still))

        # 16 葵: モーターでホイールを回すと……
        self.seg("16")
        ghost = DashedLine(C, C + UP * 3.0, color=GREY_B, stroke_width=3)
        ghost_lab = jp("最初の向き", 22, GREY_B).next_to(ghost, UP, buff=0.1)
        self.play(FadeOut(still), FadeIn(ghost), FadeIn(ghost_lab), run_time=0.6)
        self.bring_to_front(sat, wh)
        w = ValueTracker(0.0)
        wh.add_updater(lambda mob, dt: mob.rotate(w.get_value() * dt, about_point=C))
        sat.add_updater(lambda mob, dt: mob.rotate(-Iw_over_Ib * w.get_value() * dt, about_point=C))
        self.play(w.animate.set_value(4.0), run_time=2.0, rate_func=rush_into)

        # 17 茜: 機体が逆向きに回りだした！
        self.seg("17")
        arr_w = curved_arrow(C, 0.45, -0.6, 2.2, C_WHEEL)
        arr_b = curved_arrow(C, 3.0, -0.25, -1.3, C_BODY)
        tb = jp("機体は逆向き", 24, C_BODY).move_to(C + RIGHT * 2.9 + DOWN * 2.4)
        self.play(Create(arr_w), Create(arr_b), FadeIn(tb), run_time=0.8)

        # 18 葵: 反作用 → 全体の L は 0 のまま
        self.seg("18")
        tau1 = MathTex("+\\tau", font_size=44, color=C_WHEEL).next_to(L0, DOWN, buff=0.6).shift(LEFT * 1.3)
        tau2 = MathTex("-\\tau", font_size=44, color=C_BODY).next_to(L0, DOWN, buff=0.6).shift(RIGHT * 1.3)
        t1l = jp("ホイールへ", 22, C_WHEEL).next_to(tau1, DOWN, buff=0.1)
        t2l = jp("機体へ(反作用)", 22, C_BODY).next_to(tau2, DOWN, buff=0.1)
        self.play(FadeIn(VGroup(tau1, t1l), shift=LEFT * 0.2), FadeIn(VGroup(tau2, t2l), shift=RIGHT * 0.2))
        self.wait(2.5)
        bal = MathTex("I_b", "\\omega_b", "+", "I_w", "\\omega_w", "=", "0", font_size=62)
        for i in (0, 1):
            bal[i].set_color(C_BODY)
        for i in (3, 4):
            bal[i].set_color(C_WHEEL)
        bal.move_to(RIGHT * 3.3 + DOWN * 1.8)
        inner = jp("内力どうしは打ち消し合う", 24, GREY_B).next_to(bal, DOWN, buff=0.35)
        self.play(Write(bal), FadeIn(inner), run_time=1.6)

        # 19 茜: 機体はゆっくり回っとる
        self.seg("19")
        self.play(Indicate(arr_b, color=C_BODY), Indicate(tb, color=C_BODY), run_time=1.2)

        # 20 葵: I_b が大きいのでゆっくり
        self.seg("20")
        sol = MathTex("\\omega_b", "=", "-", "\\frac{I_w}{I_b}", "\\omega_w", font_size=72)
        sol[0].set_color(C_BODY); sol[4].set_color(C_WHEEL)
        sol[3][0:2].set_color(C_WHEEL); sol[3][3:5].set_color(C_BODY)
        sol.move_to(RIGHT * 3.3 + DOWN * 0.2)
        self.play(FadeOut(VGroup(tau1, tau2, t1l, t2l, inner)))
        self.play(L0.animate.scale(0.7).move_to(RIGHT * 3.3 + UP * 2.2),
                  TransformMatchingTex(bal, sol), run_time=1.6)
        note = MathTex("I_w", "\\ll", "I_b", font_size=54).next_to(sol, DOWN, buff=0.7)
        note[0].set_color(C_WHEEL); note[2].set_color(C_BODY)
        note2 = jp("→ 機体はゆっくり回る", 28).next_to(note, DOWN, buff=0.3)
        self.play(Write(note))
        self.play(FadeIn(note2, shift=UP * 0.2))

        # 21 葵: ホイールを止めると機体も止まる
        self.seg("21")
        self.play(FadeOut(VGroup(arr_w, arr_b, tb, note, note2)), run_time=0.5)
        self.play(w.animate.set_value(0.0), run_time=2.0, rate_func=smooth)
        wh.clear_updaters()
        sat.clear_updaters()
        stop = jp("ホイール停止 → 機体も停止", 28, C_L).move_to(RIGHT * 3.3 + DOWN * 1.6)
        self.play(FadeIn(stop, shift=UP * 0.2), run_time=0.6)

        # 22 茜: 向きが変わったまま止まった
        self.seg("22")
        ant = sat[2].get_center()
        now_line = Line(C, C + (ant - C) / np.linalg.norm(ant - C) * 2.2, color=C_L, stroke_width=4)
        delta = (angle_of_vector(now_line.get_vector()) - PI / 2 + PI) % TAU - PI
        arc = Arc(radius=1.6, start_angle=PI / 2, angle=delta, arc_center=C, color=C_L, stroke_width=5)
        turned = jp("向きが変わった！", 28, C_L).next_to(stop, DOWN, buff=0.35)
        self.play(Create(now_line), Create(arc), FadeIn(turned), run_time=1.0)

        # 23 葵: 燃料なしで姿勢制御
        self.seg("23")
        fuel = jp("燃料なしで姿勢制御できる", 32, C_WHEEL, weight=BOLD).next_to(turned, DOWN, buff=0.45)
        self.play(FadeIn(fuel, shift=UP * 0.2))
        self.play(Circumscribe(fuel, color=C_WHEEL), run_time=1.2)
        self.hold()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.8)
