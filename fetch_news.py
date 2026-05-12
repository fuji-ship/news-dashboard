import feedparser
import json
import anthropic
import requests
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic()

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

FEEDS = {
    "AI": [
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
        ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ],
    "投資・経済": [
        ("NHK ビジネス", "https://www3.nhk.or.jp/rss/news/cat4.xml"),
        ("ZUU online", "https://zuuonline.com/feed"),
    ],
    "仮想通貨": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("CoinTelegraph", "https://cointelegraph.com/rss"),
        ("あたらしい経済", "https://www.neweconomy.jp/feed"),
    ],
    "お金・資産形成": [
        ("東洋経済オンライン", "https://toyokeizai.net/list/feed/rss"),
    ],
    "書籍・ビジネス": [
        ("SERENDIP（書籍要約）", "https://www.serendip.site/feed"),
        ("ダイヤモンド・オンライン", "https://diamond.jp/list/rss"),
        ("プレジデントオンライン", "https://president.jp/list/rss"),
        ("ライフハッカー", "https://www.lifehacker.jp/feed/index.xml"),
        ("日経ビジネス", "https://business.nikkei.com/rss/sns/nb.rdf"),
    ],
}

def summarize(title, text):
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": f"以下の記事を日本語で2〜3文に要約してください。\nタイトル：{title}\n本文：{text[:800]}"}]
        )
        return msg.content[0].text
    except:
        return "要約を取得できませんでした。"

def fetch_articles(feed_name, url, max=5):
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
        d = feedparser.parse(r.content)
        articles = []
        for entry in d.entries[:max]:
            title = entry.get("title", "タイトルなし")
            link = entry.get("link", "#")
            summary_raw = entry.get("summary", entry.get("description", ""))
            published = entry.get("published", "")
            summary = summarize(title, summary_raw)
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
                "source": feed_name,
            })
        return articles
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
        return []

def build_html(data):
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    tabs_html = ""
    panels_html = ""
    category_colors = {
        "AI": "#6366f1",
        "投資・経済": "#10b981",
        "仮想通貨": "#f59e0b",
        "お金・資産形成": "#ec4899",
        "書籍・ビジネス": "#8b5cf6",
    }
    for i, (cat, articles) in enumerate(data.items()):
        color = category_colors.get(cat, "#6366f1")
        active = "active" if i == 0 else ""
        tabs_html += f'<button class="tab {active}" onclick="switchTab(\'{cat}\')" data-cat="{cat}" style="--accent:{color}">{cat}<span class="count">{len(articles)}</span></button>'
        cards_html = ""
        for a in articles:
            cards_html += f'''
            <div class="card">
                <div class="card-source">{a["source"]}</div>
                <a class="card-title" href="{a["link"]}" target="_blank">{a["title"]}</a>
                <p class="card-summary">{a["summary"]}</p>
                <div class="card-meta">{a["published"][:16] if a["published"] else ""}</div>
            </div>'''
        display = "block" if i == 0 else "none"
        panels_html += f'<div class="panel" id="panel-{cat}" style="display:{display}">{cards_html}</div>'

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily News Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #0f0f13;
    --surface: #1a1a24;
    --surface2: #22222f;
    --border: #2e2e3e;
    --text: #e8e8f0;
    --muted: #888899;
    --radius: 12px;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Noto Sans JP', sans-serif; min-height: 100vh; }}
  header {{ padding: 32px 40px 0; }}
  .header-top {{ display: flex; align-items: baseline; gap: 16px; margin-bottom: 6px; }}
  .logo {{ font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #fff; }}
  .updated {{ font-size: 12px; color: var(--muted); }}
  .tabs {{ display: flex; gap: 8px; padding: 24px 40px 0; flex-wrap: wrap; }}
  .tab {{ background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 10px 20px; border-radius: 999px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all .2s; font-family: 'Noto Sans JP', sans-serif; }}
  .tab:hover {{ border-color: var(--accent); color: var(--text); }}
  .tab.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
  .count {{ background: rgba(255,255,255,.2); border-radius: 999px; padding: 1px 8px; font-size: 11px; }}
  .main {{ padding: 24px 40px 60px; }}
  .panel {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; display: flex; flex-direction: column; gap: 10px; transition: border-color .2s, transform .2s; }}
  .card:hover {{ border-color: #444466; transform: translateY(-2px); }}
  .card-source {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }}
  .card-title {{ font-size: 15px; font-weight: 700; color: var(--text); text-decoration: none; line-height: 1.5; }}
  .card-title:hover {{ color: #a5b4fc; }}
  .card-summary {{ font-size: 13px; color: var(--muted); line-height: 1.7; flex: 1; }}
  .card-meta {{ font-size: 11px; color: #555566; }}
  @media(max-width:600px) {{ .tabs,.main,header {{ padding-left:16px; padding-right:16px; }} .panel {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <div class="header-top">
    <span class="logo">Daily News</span>
    <span class="updated">更新：{now}</span>
  </div>
</header>
<div class="tabs">{tabs_html}</div>
<div class="main">{panels_html}</div>
<script>
function switchTab(cat) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.style.display = 'none');
  document.querySelector(`[data-cat="${{cat}}"]`).classList.add('active');
  document.getElementById(`panel-${{cat}}`).style.display = 'grid';
}}
</script>
</body>
</html>'''

def main():
    print("ニュース収集中...")
    all_data = {}
    for cat, feeds in FEEDS.items():
        articles = []
        for name, url in feeds:
            print(f"  取得中: {name}")
            articles.extend(fetch_articles(name, url))
        all_data[cat] = articles

    output = Path.home() / "news-dashboard" / "index.html"
    output.write_text(build_html(all_data), encoding="utf-8")
    print(f"完了！ファイル: {output}")
    import subprocess
    subprocess.run(["open", str(output)])

if __name__ == "__main__":
    main()
