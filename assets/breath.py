#!/usr/bin/env python3
"""호흡 단위 줄나눔 — 프롬프터 {{BLOCKS}} 생성 전용.

왜 생성 시점인가.
  프롬프터의 「↵ 호흡 나누기」 버튼은 **낱말 편집기가 올린 텍스트만** 다룬다.
  설교자는 보통 몇 낱말만 끌어서 고르므로 끊을 자리가 없고, 버튼은 아무 일도
  하지 않는 것처럼 보인다. 실사용에서 설교자가 두 번 "동작하지 않음"으로 신고했다.
  → 줄나눔은 **원고를 HTML로 옮길 때 미리** 끝내 둔다. 버튼은 뒷손질용으로만 남는다.

규칙 (강단 낭독 기준)
  한 줄 = 한 호흡. 어절을 쌓다가 아래 중 하나에서 끊는다.
    ① 문장 끝(. ! ? …)
    ② 쉼표 — 단, 이미 MIN을 채웠을 때
    ③ 연결어미 — 단, 뒤가 보조용언이면 끊지 않는다("관할하고 있는"을 쪼개지 않기 위함)
    ④ MAX를 **넘기 직전**. 넘은 뒤에 재면 37~38자 줄이 그대로 확정된다.

  설교자 낱말은 한 글자도 바꾸지 않는다. 줄만 나눈다.
"""
import re

SENT = re.compile(r'[.!?…]["”’\']?$')
CONN = re.compile(
    r'(습니다|입니다|합니다|하십니다|셨습니다|것입니다|하겠습니다|같았습니다'
    r'|지만|는데|면서|으므로|므로|때문에|라고|하여|길래|으며|이며|거나|든지'
    r'|도록|더니|아서|어서|여서|으니|으면|다면)[,]?$')
AUX = re.compile(r'^(?:하|했|해|계|있|없|말|싶|드|버|못|같|되|주|보)')  # 보조용언
MIN, MAX = 12, 32


def breath(line: str, mn: int = MIN, mx: int = MAX) -> list[str]:
    """한 줄을 호흡 단위 여러 줄로. 낱말 무수정."""
    w = [t for t in re.sub(r'\s+', ' ', line).strip().split(' ') if t]
    out, cur = [], []
    L = lambda a: len(' '.join(a))
    for i, tok in enumerate(w):
        if cur and L(cur) >= mn and L(cur + [tok]) > mx:
            out.append(' '.join(cur)); cur = []
        cur.append(tok)
        nx = w[i + 1] if i + 1 < len(w) else ''
        if not nx:
            break
        if SENT.search(tok) or (L(cur) >= mn and
                                (tok.endswith(',') or (CONN.search(tok) and not AUX.match(nx)))):
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    return out or [line.strip()]


def to_blocks_html(md: str, esc=None) -> str:
    """마크다운 원고 → 프롬프터 block-body HTML.

    빈 줄 = 문단 경계, '>' 로 시작하면 blockquote(성경 인용).
    각 줄은 breath()로 호흡 분할 후 <br> 로 잇는다.
    """
    import html as _h
    esc = esc or _h.escape
    out, buf, q = [], [], []

    def fp():
        if buf:
            out.append("      <p>" + "<br>\n      ".join(buf) + "</p>"); buf.clear()

    def fq():
        if q:
            out.append("      <blockquote>" + "<br>\n      ".join(q) + "</blockquote>"); q.clear()

    for raw in md.split("\n"):
        s = raw.rstrip()
        if s.lstrip().startswith("<sub>"):
            continue
        if not s.strip():
            fq(); fp(); continue
        if s.lstrip().startswith(">"):
            fp()
            # 성경 인용은 짧으므로 원 줄나눔을 존중하되 과하게 길면 나눈다
            q.extend(esc(x) for x in breath(s.lstrip()[1:].strip()))
        else:
            fq()
            buf.extend(esc(x) for x in breath(s.strip()))
    fq(); fp()
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    t = sys.stdin.read()
    ls = breath(t)
    print(f"— {len(ls)}줄 · 최장 {max(len(x) for x in ls)}자")
    for x in ls:
        print(f"  {len(x):>3}  {x}")
