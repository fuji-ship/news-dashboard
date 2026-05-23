import feedparser
import json
import re
import hashlib
import requests
from datetime import datetime
from pathlib import Path

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

CATEGORY_COLORS = {
    "AI": "#6366f1",
    "投資・経済": "#10b981",
    "仮想通貨": "#f59e0b",
    "お金・資産形成": "#ec4899",
    "書籍・ビジネス": "#8b5cf6",
    "保存済み": "#f43f5e",
}


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def article_id(link):
    return hashlib.md5((link or "").encode("utf-8")).hexdigest()[:12]


def collect_raw_entries():
    items = []
    for cat, feeds in FEEDS.items():
        for name, url in feeds:
            print(f"  取得中: {name}")
            try:
                r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
                r.raise_for_status()
                d = feedparser.parse(r.content)
                for entry in d.entries[:5]:
                    items.append({
                        "category": cat,
                        "source": name,
                        "title": entry.get("title", "タイトルなし"),
                        "link": entry.get("link", "#"),
                        "raw": strip_html(entry.get("summary", entry.get("description", ""))),
                        "published": entry.get("published", ""),
                    })
            except Exception as e:
                print(f"  Error fetching {name}: {e}")
    return items


def process(item):
    return {
        "id": article_id(item["link"]),
        "title": item["title"],
        "link": item["link"],
        "summary": item["raw"],
        "published": item["published"],
        "source": item["source"],
        "category": item["category"],
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily News Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f0f13;
    --surface: #1a1a24;
    --surface2: #22222f;
    --border: #2e2e3e;
    --text: #e8e8f0;
    --muted: #888899;
    --radius: 12px;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Noto Sans JP', sans-serif; min-height: 100vh; }
  header { padding: 32px 40px 0; }
  .header-top { display: flex; align-items: center; gap: 16px; margin-bottom: 6px; }
  .logo { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; color: #fff; }
  .updated { font-size: 12px; color: var(--muted); }
  .header-spacer { flex: 1; }
  .update-btn { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 999px; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all .2s; font-family: 'Noto Sans JP', sans-serif; white-space: nowrap; }
  .update-btn:hover { border-color: #6366f1; color: #6366f1; }
  .tabs { display: flex; gap: 8px; padding: 24px 40px 0; flex-wrap: wrap; }
  .tab { background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 10px 20px; border-radius: 999px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: all .2s; font-family: 'Noto Sans JP', sans-serif; }
  .tab:hover { border-color: var(--accent); color: var(--text); }
  .tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .count { background: rgba(255,255,255,.2); border-radius: 999px; padding: 1px 8px; font-size: 11px; }
  .main { padding: 24px 40px 60px; }
  .panel { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 20px 16px; display: flex; flex-direction: column; gap: 10px; transition: border-color .2s, transform .2s; position: relative; cursor: pointer; }
  .card:hover { border-color: #444466; transform: translateY(-2px); }
  .card-source { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; padding-right: 32px; }
  .card-title { font-size: 15px; font-weight: 700; color: var(--text); line-height: 1.5; }
  .card-summary { font-size: 13px; color: var(--muted); line-height: 1.7; flex: 1; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
  .card-meta { font-size: 11px; color: #555566; }
  .save-btn { position: absolute; top: 12px; right: 12px; background: transparent; border: none; color: var(--muted); cursor: pointer; font-size: 20px; line-height: 1; padding: 6px 8px; border-radius: 6px; transition: color .15s, background .15s; }
  .save-btn:hover { background: var(--surface2); color: #f59e0b; }
  .save-btn.saved { color: #f59e0b; }
  .empty-state { grid-column: 1 / -1; text-align: center; padding: 80px 20px; color: var(--muted); font-size: 14px; line-height: 1.8; }
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.75); display: none; align-items: flex-start; justify-content: center; padding: 40px 20px; z-index: 100; overflow-y: auto; }
  .modal-overlay.open { display: flex; }
  .modal { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; max-width: 720px; width: 100%; padding: 36px 36px 32px; position: relative; }
  .modal-close { position: absolute; top: 14px; right: 18px; background: transparent; border: none; color: var(--muted); font-size: 30px; cursor: pointer; line-height: 1; padding: 4px 10px; border-radius: 8px; }
  .modal-close:hover { background: var(--surface2); color: var(--text); }
  .modal-source { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 12px; }
  .modal-title { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.5; margin-bottom: 10px; }
  .modal-meta { font-size: 12px; color: #555566; margin-bottom: 22px; }
  .modal-summary { font-size: 15px; color: var(--text); line-height: 1.9; white-space: pre-wrap; }
  .modal-actions { display: flex; gap: 10px; margin-top: 28px; flex-wrap: wrap; }
  .btn { padding: 10px 20px; border-radius: 999px; font-size: 14px; font-weight: 500; cursor: pointer; border: 1px solid var(--border); font-family: 'Noto Sans JP', sans-serif; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: all .15s; }
  .btn-primary { background: #6366f1; border-color: #6366f1; color: #fff; }
  .btn-primary:hover { background: #5458e0; }
  .btn-secondary { background: var(--surface2); color: var(--text); }
  .btn-secondary:hover { border-color: #f59e0b; color: #f59e0b; }
  .btn-secondary.saved { border-color: #f59e0b; color: #f59e0b; }
  /* update modal */
  .update-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.75); display: none; align-items: center; justify-content: center; padding: 20px; z-index: 200; }
  .update-overlay.open { display: flex; }
  .update-modal { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; max-width: 500px; width: 100%; padding: 32px; position: relative; }
  .update-modal h3 { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 24px; }
  .update-steps { list-style: none; display: flex; flex-direction: column; gap: 20px; }
  .update-steps li { display: flex; gap: 14px; align-items: flex-start; font-size: 14px; color: var(--text); line-height: 1.6; }
  .step-num { background: #6366f1; color: #fff; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
  .step-body { flex: 1; }
  .cmd-box { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-top: 10px; display: flex; align-items: center; gap: 10px; }
  .cmd-text { font-family: monospace; font-size: 13px; color: #a5b4fc; flex: 1; }
  .copy-btn { background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-family: 'Noto Sans JP', sans-serif; white-space: nowrap; transition: all .15s; }
  .copy-btn:hover { border-color: #6366f1; color: #6366f1; }
  .copy-btn.copied { border-color: #10b981; color: #10b981; }
  @media(max-width:600px) { .tabs,.main,header { padding-left:16px; padding-right:16px; } .panel { grid-template-columns: 1fr; } .modal { padding: 28px 22px 24px; } .update-modal { padding: 24px 18px; } }
</style>
</head>
<body>
<header>
  <div class="header-top">
    <span class="logo">Daily News</span>
    <span class="updated">更新：__DATE__</span>
    <div class="header-spacer"></div>
    <button class="update-btn" id="update-btn">🔄 ニュース更新</button>
  </div>
</header>
<div class="tabs" id="tabs"></div>
<div class="main" id="main"></div>

<div class="modal-overlay" id="modal">
  <div class="modal" role="dialog" aria-modal="true">
    <button class="modal-close" aria-label="閉じる" id="modal-close">×</button>
    <div class="modal-source" id="modal-source"></div>
    <h2 class="modal-title" id="modal-title"></h2>
    <div class="modal-meta" id="modal-meta"></div>
    <p class="modal-summary" id="modal-summary"></p>
    <div class="modal-actions">
      <a class="btn btn-primary" id="modal-link" target="_blank" rel="noopener">元記事を読む →</a>
      <button class="btn btn-secondary" id="modal-save">☆ 保存</button>
    </div>
  </div>
</div>

<div class="update-overlay" id="update-overlay">
  <div class="update-modal" role="dialog" aria-modal="true">
    <button class="modal-close" id="update-modal-close">×</button>
    <h3>ニュースを最新情報に更新する</h3>
    <ol class="update-steps">
      <li>
        <span class="step-num">1</span>
        <div class="step-body">ターミナルアプリを開く<br><span style="font-size:12px;color:var(--muted)">Mac: Spotlight（⌘Space）で「Terminal」を検索</span></div>
      </li>
      <li>
        <span class="step-num">2</span>
        <div class="step-body">
          以下のコマンドをコピーして貼り付ける
          <div class="cmd-box">
            <span class="cmd-text">python3 ~/news-dashboard/fetch_news.py</span>
            <button class="copy-btn" id="copy-cmd-btn">コピー</button>
          </div>
        </div>
      </li>
      <li>
        <span class="step-num">3</span>
        <div class="step-body">Enter を押して実行し、完了後にページを再読み込み（⌘R）する</div>
      </li>
    </ol>
  </div>
</div>

<script>
const ARTICLES = __ARTICLES__;
const CATEGORIES = __CATEGORIES__;
const COLORS = __COLORS__;
const STORAGE_KEY = "newsDashboard.saved.v1";
const SAVED_LABEL = "保存済み";

let savedMap = {};
try { savedMap = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch (e) { savedMap = {}; }

let activeCat = CATEGORIES[0];
let currentArticleId = null;

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[m]));
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(savedMap));
}

function articlesFor(cat) {
  if (cat === SAVED_LABEL) {
    return Object.values(savedMap).sort((a, b) => (b.savedAt || 0) - (a.savedAt || 0));
  }
  return ARTICLES.filter(a => a.category === cat);
}

function isSaved(id) { return Object.prototype.hasOwnProperty.call(savedMap, id); }

function renderTabs() {
  const all = [...CATEGORIES, SAVED_LABEL];
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = all.map(cat => {
    const color = COLORS[cat] || "#888899";
    const count = articlesFor(cat).length;
    const active = cat === activeCat ? "active" : "";
    return `<button class="tab ${active}" data-cat="${esc(cat)}" style="--accent:${color}">${esc(cat)}<span class="count">${count}</span></button>`;
  }).join("");
  tabs.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => { activeCat = btn.dataset.cat; render(); });
  });
}

function cardHtml(a) {
  const saved = isSaved(a.id) ? "saved" : "";
  const star = isSaved(a.id) ? "★" : "☆";
  const pub = a.published ? esc(a.published.slice(0, 16)) : "";
  return `
    <div class="card" data-id="${esc(a.id)}">
      <button class="save-btn ${saved}" data-id="${esc(a.id)}" title="${isSaved(a.id) ? "保存解除" : "保存"}">${star}</button>
      <div class="card-source">${esc(a.source)}</div>
      <div class="card-title">${esc(a.title)}</div>
      <p class="card-summary">${esc(a.summary)}</p>
      <div class="card-meta">${pub}</div>
    </div>`;
}

function renderPanel() {
  const items = articlesFor(activeCat);
  const main = document.getElementById("main");
  if (items.length === 0) {
    const msg = activeCat === SAVED_LABEL
      ? "保存した記事はまだありません。<br>各カードの☆ボタンで保存できます。"
      : "記事がありません。";
    main.innerHTML = `<div class="panel"><div class="empty-state">${msg}</div></div>`;
    return;
  }
  main.innerHTML = `<div class="panel">${items.map(cardHtml).join("")}</div>`;
  main.querySelectorAll(".card").forEach(c => {
    c.addEventListener("click", e => {
      if (e.target.closest(".save-btn")) return;
      openModal(c.dataset.id);
    });
  });
  main.querySelectorAll(".save-btn").forEach(b => {
    b.addEventListener("click", e => {
      e.stopPropagation();
      toggleSave(b.dataset.id);
    });
  });
}

function render() {
  renderTabs();
  renderPanel();
}

function findArticle(id) {
  return savedMap[id] || ARTICLES.find(a => a.id === id);
}

function openModal(id) {
  const a = findArticle(id);
  if (!a) return;
  currentArticleId = id;
  document.getElementById("modal-source").textContent = `${a.source} · ${a.category}`;
  document.getElementById("modal-title").textContent = a.title;
  document.getElementById("modal-meta").textContent = a.published || "";
  document.getElementById("modal-summary").textContent = a.summary;
  document.getElementById("modal-link").href = a.link;
  updateModalSaveBtn();
  document.getElementById("modal").classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  document.getElementById("modal").classList.remove("open");
  document.body.style.overflow = "";
  currentArticleId = null;
}

function toggleSave(id) {
  if (isSaved(id)) {
    delete savedMap[id];
  } else {
    const a = ARTICLES.find(x => x.id === id) || savedMap[id];
    if (!a) return;
    savedMap[id] = { ...a, savedAt: Date.now() };
  }
  persist();
  render();
  if (currentArticleId === id) updateModalSaveBtn();
}

function updateModalSaveBtn() {
  const btn = document.getElementById("modal-save");
  const saved = isSaved(currentArticleId);
  btn.textContent = saved ? "★ 保存済み" : "☆ 保存";
  btn.classList.toggle("saved", saved);
}

document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("modal").addEventListener("click", e => {
  if (e.target.id === "modal") closeModal();
});
document.getElementById("modal-save").addEventListener("click", () => {
  if (currentArticleId) toggleSave(currentArticleId);
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    closeModal();
    document.getElementById("update-overlay").classList.remove("open");
  }
});

// update modal
document.getElementById("update-btn").addEventListener("click", () => {
  document.getElementById("update-overlay").classList.add("open");
});
document.getElementById("update-modal-close").addEventListener("click", () => {
  document.getElementById("update-overlay").classList.remove("open");
});
document.getElementById("update-overlay").addEventListener("click", e => {
  if (e.target.id === "update-overlay") document.getElementById("update-overlay").classList.remove("open");
});
document.getElementById("copy-cmd-btn").addEventListener("click", () => {
  navigator.clipboard.writeText("python3 ~/news-dashboard/fetch_news.py").then(() => {
    const btn = document.getElementById("copy-cmd-btn");
    btn.textContent = "コピー済み!";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "コピー"; btn.classList.remove("copied"); }, 2000);
  });
});

render();
</script>
</body>
</html>"""


def build_html(articles, categories):
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return (HTML_TEMPLATE
        .replace("__ARTICLES__", json.dumps(articles, ensure_ascii=False))
        .replace("__CATEGORIES__", json.dumps(categories, ensure_ascii=False))
        .replace("__COLORS__", json.dumps(CATEGORY_COLORS, ensure_ascii=False))
        .replace("__DATE__", now))


def main():
    print("ニュース収集中...")
    raw_items = collect_raw_entries()
    articles = [process(item) for item in raw_items]
    categories = list(FEEDS.keys())
    output = Path.home() / "news-dashboard" / "index.html"
    output.write_text(build_html(articles, categories), encoding="utf-8")
    print(f"完了！ファイル: {output}（記事数: {len(articles)}）")
    import subprocess
    subprocess.run(["open", str(output)])


if __name__ == "__main__":
    main()
