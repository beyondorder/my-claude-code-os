#!/usr/bin/env python3
"""skill-usage.log -> 화려한 HTML 리포트 생성 & 브라우저로 열기.

로그 형식 (탭 구분): "<시각>\t<skill 이름>\t<인자>"
  - skill 이름 필드는 hook에서 %-20s로 패딩되어 있을 수 있어 strip() 처리한다.
  - 인자 필드는 비어 있을 수 있다.

스크립트 위치(.claude/skills/skill-report/)를 기준으로 프로젝트 루트를 찾으므로
실행 디렉터리와 무관하게 동작한다.
"""
import html
import os
import sys
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path

# 이 파일: <root>/.claude/skills/skill-report/generate_report.py  -> parents[3] == <root>
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_PATH = PROJECT_ROOT / ".claude" / "skill-usage.log"
REPORT_PATH = PROJECT_ROOT / ".claude" / "skill-usage-report.html"


def parse_log(path: Path):
    """로그를 (시각, skill, 인자) 튜플 리스트로 파싱한다."""
    rows = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        ts = parts[0].strip() if len(parts) > 0 else ""
        name = parts[1].strip() if len(parts) > 1 else "(unknown)"
        args = parts[2].strip() if len(parts) > 2 else ""
        rows.append((ts, name, args))
    return rows


def build_html(rows):
    total = len(rows)
    counts = Counter(name for _, name, _ in rows)
    unique = len(counts)
    first_ts = rows[0][0] if rows else "—"
    last_ts = rows[-1][0] if rows else "—"
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- 랭킹 막대 (사용 횟수 내림차순) ----
    max_count = max(counts.values()) if counts else 1
    palette = [
        "#7c3aed", "#2563eb", "#0891b2", "#059669",
        "#d97706", "#dc2626", "#db2777", "#4f46e5",
    ]
    bars = []
    for i, (name, cnt) in enumerate(counts.most_common()):
        pct = cnt / max_count * 100
        color = palette[i % len(palette)]
        bars.append(f"""
          <div class="bar-row">
            <div class="bar-label">{html.escape(name)}</div>
            <div class="bar-track">
              <div class="bar-fill" style="--target:{pct:.1f}%; --c:{color};">
                <span class="bar-count">{cnt}</span>
              </div>
            </div>
          </div>""")
    bars_html = "".join(bars) if bars else '<p class="empty">아직 기록된 skill 사용이 없습니다.</p>'

    # ---- 타임라인 테이블 (최신 우선) ----
    trows = []
    for ts, name, args in reversed(rows):
        args_cell = html.escape(args) if args else '<span class="muted">—</span>'
        trows.append(f"""
          <tr>
            <td class="ts">{html.escape(ts)}</td>
            <td><span class="pill">{html.escape(name)}</span></td>
            <td class="args">{args_cell}</td>
          </tr>""")
    table_html = "".join(trows) if trows else (
        '<tr><td colspan="3" class="empty">기록 없음</td></tr>'
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skill 사용 리포트</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{ color-scheme: dark; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple SD Gothic Neo", Roboto, sans-serif;
    min-height: 100vh; color: #e5e7eb; padding: 48px 24px;
    background: radial-gradient(1200px 800px at 10% -10%, #1e3a8a44, transparent),
                radial-gradient(1000px 700px at 110% 10%, #7c3aed44, transparent),
                linear-gradient(160deg, #0b1020 0%, #0f172a 60%, #020617 100%);
    background-attachment: fixed;
  }}
  .wrap {{ max-width: 960px; margin: 0 auto; }}
  header {{ text-align: center; margin-bottom: 40px; }}
  h1 {{
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }}
  .subtitle {{ color: #94a3b8; margin-top: 8px; font-size: 0.95rem; }}

  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 18px; margin-bottom: 40px; }}
  .card {{
    background: rgba(255,255,255,0.05); backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 22px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35); transition: transform .2s ease, border-color .2s ease;
  }}
  .card:hover {{ transform: translateY(-4px); border-color: rgba(167,139,250,0.5); }}
  .card .num {{ font-size: 2.4rem; font-weight: 800; line-height: 1;
    background: linear-gradient(90deg, #c4b5fd, #93c5fd);
    -webkit-background-clip: text; background-clip: text; color: transparent; }}
  .card .lbl {{ color: #94a3b8; font-size: 0.85rem; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.06em; }}

  .panel {{
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px; padding: 28px; margin-bottom: 32px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  }}
  .panel h2 {{ font-size: 1.2rem; margin-bottom: 22px; display: flex; align-items: center; gap: 10px; }}
  .panel h2::before {{ content: ""; width: 6px; height: 22px; border-radius: 4px;
    background: linear-gradient(180deg, #a78bfa, #60a5fa); display: inline-block; }}

  .bar-row {{ display: grid; grid-template-columns: 160px 1fr; align-items: center; gap: 14px; margin-bottom: 14px; }}
  .bar-label {{ font-size: 0.9rem; color: #cbd5e1; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .bar-track {{ background: rgba(255,255,255,0.06); border-radius: 10px; height: 30px; overflow: hidden; }}
  .bar-fill {{
    height: 100%; width: 0; border-radius: 10px;
    background: linear-gradient(90deg, var(--c), color-mix(in srgb, var(--c) 55%, white));
    display: flex; align-items: center; justify-content: flex-end; padding-right: 12px;
    animation: grow 1.1s cubic-bezier(.22,1,.36,1) forwards;
    box-shadow: 0 2px 12px color-mix(in srgb, var(--c) 60%, transparent);
  }}
  @keyframes grow {{ to {{ width: var(--target); }} }}
  .bar-count {{ font-weight: 700; font-size: 0.85rem; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.4); }}

  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ text-align: left; color: #94a3b8; font-weight: 600; padding: 10px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.12); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
  td {{ padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
  tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .ts {{ color: #94a3b8; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .pill {{ background: rgba(124,58,237,0.25); border: 1px solid rgba(167,139,250,0.4);
    color: #ddd6fe; padding: 3px 12px; border-radius: 999px; font-weight: 600; font-size: 0.82rem; }}
  .args {{ color: #cbd5e1; }}
  .muted {{ color: #475569; }}
  .empty {{ text-align: center; color: #64748b; padding: 20px; }}

  footer {{ text-align: center; color: #475569; font-size: 0.8rem; margin-top: 40px; }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>✦ Skill 사용 리포트</h1>
      <p class="subtitle">my-claude-code-os · {generated} 생성</p>
    </header>

    <section class="cards">
      <div class="card"><div class="num">{total}</div><div class="lbl">전체 호출</div></div>
      <div class="card"><div class="num">{unique}</div><div class="lbl">사용한 skill 종류</div></div>
      <div class="card"><div class="num" style="font-size:1.1rem">{html.escape(first_ts)}</div><div class="lbl">첫 기록</div></div>
      <div class="card"><div class="num" style="font-size:1.1rem">{html.escape(last_ts)}</div><div class="lbl">마지막 기록</div></div>
    </section>

    <section class="panel">
      <h2>skill별 사용 횟수</h2>
      {bars_html}
    </section>

    <section class="panel">
      <h2>전체 타임라인 (최신순)</h2>
      <table>
        <thead><tr><th>시각</th><th>Skill</th><th>인자</th></tr></thead>
        <tbody>{table_html}</tbody>
      </table>
    </section>

    <footer>Generated by /skill-report · Claude Code OS 실습</footer>
  </div>
</body>
</html>"""


def main():
    rows = parse_log(LOG_PATH)
    REPORT_PATH.write_text(build_html(rows), encoding="utf-8")

    # Claude가 사용자에게 그대로 전달할 수 있도록 요약을 stdout으로 출력
    counts = Counter(name for _, name, _ in rows)
    print(f"로그 파일   : {LOG_PATH}")
    print(f"리포트 경로 : {REPORT_PATH}")
    print(f"전체 호출   : {len(rows)}회, 고유 skill {len(counts)}종")
    if counts:
        top = ", ".join(f"{n}({c})" for n, c in counts.most_common(5))
        print(f"상위 사용    : {top}")
    else:
        print("주의: 기록이 비어 있습니다. skill을 한 번 사용한 뒤 다시 실행하세요.")

    # 브라우저로 열기 (실패해도 리포트 파일은 이미 생성됨)
    opened = webbrowser.open(REPORT_PATH.as_uri())
    print(f"브라우저 열기: {'성공' if opened else '실패 (위 경로를 직접 열어주세요)'}")


if __name__ == "__main__":
    sys.exit(main())
