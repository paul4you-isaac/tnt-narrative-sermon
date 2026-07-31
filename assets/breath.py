#!/usr/bin/env python3
"""호흡 단위 줄나눔 — 프롬프터 {{BLOCKS}} 생성 전용.

★ 원칙: **문법이 길이보다 앞선다.**
  강단에서는 긴 줄보다 어절 묶음 안에서 끊긴 자리가 더 나쁘다.
  "용납할 수 / 없었습니다"에서 눈이 멈추면 문장이 무너진다.
  40자를 한 호흡에 읽는 것은 되지만, 본용언과 보조용언 사이의 끊김은 안 된다.

끊는 자리는 셋뿐이다.
  ① 문장 끝 (. ! ? …)
  ② 쉼표 — 이미 MIN을 채웠을 때
  ③ 연결어미·절 닫는 형태 — 이미 MIN을 채웠고, **뒤가 보조용언이 아닐 때**
     (…습니다/…지만/…면서 류 + 처럼·같이·듯이·만큼·려고·고 등 절 경계)

길이로 강제하지 않는다. 끊을 자리가 없으면 **길어도 그냥 둔다.**
  (v1: MAX=32를 강제해 약 25곳이 어절 묶음 안에서 끊겼다. 설교자가 원고에서 발견했다.)

왜 생성 시점인가.
  프롬프터의 「↵ 호흡 나누기」 버튼은 낱말 편집기가 올린 텍스트만 다룬다. 설교자는
  보통 몇 낱말만 끌어서 고르므로 끊을 자리가 없고, 버튼은 동작하지 않는 것처럼 보인다
  (실사용에서 두 번 신고됨). → 줄나눔은 원고를 HTML로 옮길 때 미리 끝낸다.

설교자 낱말은 한 글자도 바꾸지 않는다. 줄만 나눈다.
"""
import re

SENT = re.compile(r'[.!?…]["”’\']?$')
CONN = re.compile(
    r'(습니다|입니다|합니다|하십니다|셨습니다|것입니다|하겠습니다|같았습니다'
    r'|지만|는데|면서|으므로|므로|때문에|라고|하여|길래|으며|이며|거나|든지'
    r'|도록|더니|아서|어서|여서|서서|으니|으면|다면'
    # 절을 닫는 비교·목적·나열 형태 — 이것이 없으면 60~70자 줄이 남는다.
    # ⚠ 바른 '처럼'은 절을 닫는 '것처럼'만. 명사 비유('벽처럼')에서 끊으면
    #    비유가 수식하는 말과 갈라진다.
    r'|것처럼|것같이|듯이|만큼|채로|려고|고서|고)[,]?$')
# 보조용언·의존 형태 — 이 앞에서 끊으면 어절 묶음이 갈라진다
AUX = re.compile(r'^(?:하|했|해|계|있|없|말|싶|드|버|못|같|되|주|보|만|줄|채|양|법|듯|뻔|via)')
MIN = 12


def breath(line: str, mn: int = MIN) -> list[str]:
    """한 줄을 호흡 단위 여러 줄로. 낱말 무수정. 길이로 강제 분할하지 않는다."""
    w = [t for t in re.sub(r'\s+', ' ', line).strip().split(' ') if t]
    out, cur = [], []
    L = lambda a: len(' '.join(a))
    for i, tok in enumerate(w):
        cur.append(tok)
        nx = w[i + 1] if i + 1 < len(w) else ''
        if not nx:
            break
        if SENT.search(tok):
            out.append(' '.join(cur)); cur = []
        elif L(cur) >= mn and tok.endswith(','):
            out.append(' '.join(cur)); cur = []
        elif L(cur) >= mn and CONN.search(tok) and not AUX.match(nx):
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    return out or [line.strip()]


def to_blocks_html(md: str, esc=None) -> str:
    """마크다운 원고 → 프롬프터 block-body HTML.

    빈 줄 = 문단 경계, '>' 로 시작하면 blockquote(성경 인용).
    각 줄은 breath()로 호흡 분할 후 <br> 로 잇는다.
    입력의 줄바꿈은 의미가 없다(문단 단위로 다시 이어 붙인 뒤 분할한다) —
    앞선 회차의 잘못된 줄나눔을 그대로 물려받지 않기 위함이다.
    """
    import html as _h
    esc = esc or _h.escape
    out, para, quote = [], [], []

    def flush_p():
        if para:
            lines = breath(' '.join(para))
            out.append("      <p>" + "<br>\n      ".join(esc(x) for x in lines) + "</p>")
            para.clear()

    def flush_q():
        if quote:
            out.append("      <blockquote>" +
                       "<br>\n      ".join(esc(x) for x in quote) + "</blockquote>")
            quote.clear()

    for raw in md.split("\n"):
        s = raw.rstrip()
        if s.lstrip().startswith("<sub>"):
            continue
        if not s.strip():
            flush_q(); flush_p(); continue
        if s.lstrip().startswith(">"):
            flush_p(); quote.append(s.lstrip()[1:].strip())   # 성경 인용은 원 줄나눔 존중
        else:
            flush_q(); para.append(s.strip())
    flush_q(); flush_p()
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    ls = breath(sys.stdin.read())
    print(f"— {len(ls)}줄 · 최장 {max(len(x) for x in ls)}자")
    for x in ls:
        print(f"  {len(x):>3}  {x}")
