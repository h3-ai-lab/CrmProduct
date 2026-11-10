#!/usr/bin/env python3
"""Dino CRM 手册构建脚本（中英双语、版本快照）。

用法:
  python3 build.py
      构建当前版本到 dist/
  python3 build.py --release 1.1.0 --label "5.5 版本" \
      --summary "本次上线内容..." --prd-url "https://..."
      固化新版本快照，并更新当前站点与历史版本页
  python3 build.py --list-releases
      查看已固化版本
输入:  docs/**/*.md          （中文源）
       docs/en/**/*.md       （英文源）
输出:  dist/index.html       （中文站点）
       dist/en/index.html    （英文站点）
       dist/images/*         （截图，两站共用）
       dist/versions/*       （历史版本快照与版本索引）
"""

import argparse
import html
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DIST = ROOT / "dist"
EN_DIR = "en"
RELEASES = ROOT / "releases"
RELEASE_INDEX = RELEASES / "index.json"


# ---------- 多语言配置 ----------

LANGS = {
    "zh": {
        "scan": DOCS,
        "out": "index.html",
        "html_lang": "zh-CN",
        "img_prefix": "",
        "other": "en/index.html",
        "other_label": "EN",
        "brand": "Dino CRM 手册",
        "brand_sub": "内部文档",
        "title": "Dino CRM 使用手册",
        "hero_h1": "Dino CRM 使用手册",
        "hero_p": "按任务和角色查找操作说明：一线伙伴跟着步骤做即可，管理员与超管的配置篇请切换角色筛选查看。",
        "placeholder": "搜索任务、功能或问题…",
        "chips": ["全部", "销售专员", "销售组长", "管理员", "超级管理员"],
        "stats": ["篇指南", "个模块", "当前版本"],
        "updated": "最后更新",
        "empty": "当前筛选没有匹配的手册，换个角色或关键词试试。",
        "mods": ["开始使用", "管理看板", "销售管理", "营销中心", "用户与订单", "系统管理"],
        "switch_title": "Read in English",
        "history_label": "历史版本",
        "version_tip": "当前使用手册版本",
    },
    "en": {
        "scan": DOCS / EN_DIR,
        "out": "en/index.html",
        "html_lang": "en",
        "img_prefix": "../",
        "other": "../index.html",
        "other_label": "中文",
        "brand": "Dino CRM Handbook",
        "brand_sub": "Internal docs",
        "title": "Dino CRM Handbook",
        "hero_h1": "Dino CRM Handbook",
        "hero_p": "Find guidance by task and role. Frontline teams can follow the steps as written; admins and super admins can switch the role filter to see configuration guides.",
        "placeholder": "Search a task, feature or issue…",
        "chips": ["All", "Sales Rep", "Sales Lead", "Admin", "Super Admin"],
        "stats": ["guides", "modules", "current version"],
        "updated": "Last updated",
        "empty": "No guides match the current filter. Try another role or a different keyword.",
        "mods": ["Getting Started", "Dashboard", "Sales", "Marketing", "Users & Orders", "System Admin"],
        "switch_title": "以中文阅读",
        "history_label": "Version history",
        "version_tip": "Current handbook version",
    },
}


# ---------- Markdown 解析 ----------

def parse_frontmatter(text):
    """返回 (meta_dict, body_text)。无 front-matter 时 meta 为空。"""
    meta = {}
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def inline_md(s, img_prefix=""):
    s = html.escape(s, quote=False)
    s = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: f'<img src="{img_prefix}{m.group(2)}" alt="{m.group(1)}" loading="lazy">',
        s,
    )
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md, img_prefix=""):
    """支持子集：##/### 标题、有序/无序列表、表格、引用、段落、行内格式。"""
    out, lines = [], md.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("### "):
            out.append("<h4>" + inline_md(s[4:], img_prefix) + "</h4>")
            i += 1
        elif s.startswith("## "):
            out.append("<h3>" + inline_md(s[3:], img_prefix) + "</h3>")
            i += 1
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                t = ["<table>", "<thead><tr>"]
                t += ["<th>" + inline_md(c, img_prefix) + "</th>" for c in rows[0]]
                t.append("</tr></thead><tbody>")
                for r in rows[1:]:
                    t.append("<tr>" + "".join("<td>" + inline_md(c, img_prefix) + "</td>" for c in r) + "</tr>")
                t.append("</tbody></table>")
                out.append("".join(t))
        elif s.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append('<blockquote class="note">' + inline_md(" ".join(buf), img_prefix) + "</blockquote>")
        elif re.match(r"^\d+\.\s", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>" + inline_md(x, img_prefix) + "</li>" for x in items) + "</ol>")
        elif s.startswith("- ") or s.startswith("* "):
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join("<li>" + inline_md(x, img_prefix) + "</li>" for x in items) + "</ul>")
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\d+\.\s|-\s|\*\s|\||>\s)", lines[i].strip()
            ):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>" + inline_md(" ".join(buf), img_prefix) + "</p>")
    return "\n".join(out)


# ---------- 内容收集 ----------

def load_docs(lang, img_prefix=None):
    cfg = LANGS[lang]
    base = cfg["scan"]
    if not base.exists():
        return []
    articles = []
    for f in sorted(base.rglob("*.md")):
        if f.name.startswith("_"):
            continue
        # 英文目录不在中文扫描范围之外，此处再加一道保险
        if lang == "zh" and EN_DIR in f.relative_to(DOCS).parts:
            continue
        meta, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not meta.get("id"):
            print(f"  ! 跳过（缺 id）: {f}")
            continue
        roles = [r.strip() for r in meta.get("roles", "").split(",") if r.strip()]
        articles.append({
            "id": meta["id"],
            "title": meta.get("title", meta["id"]),
            "module": meta.get("module", "其他"),
            "roles": roles,
            "updated": meta.get("updated", ""),
            "summary": meta.get("summary", ""),
            "html": md_to_html(body, cfg["img_prefix"] if img_prefix is None else img_prefix),
            "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "src": str(f.relative_to(ROOT)),
        })
    articles.sort(key=lambda a: a["id"])
    return articles


# ---------- 页面生成 ----------

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2733;--ink2:#5b6b7c;--ink3:#8a97a6;--line:#e3e8ee;
--blue:#2b5ca8;--blue2:#eef3fa;--amber:#b7791f;--amber2:#fdf6e9;--green:#2e7d5b;--radius:10px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
background:var(--bg);color:var(--ink);font-size:14.5px;line-height:1.7}
.layout{display:flex;min-height:100vh}
/* 侧栏 */
.sidebar{width:264px;flex:0 0 264px;background:var(--card);border-right:1px solid var(--line);
position:sticky;top:0;height:100vh;overflow-y:auto;padding:20px 14px 30px}
.brand{display:flex;align-items:baseline;gap:8px;padding:2px 8px 12px}
.brand b{font-size:16.5px}.brand span{font-size:11.5px;color:var(--ink3)}
.langbar{padding:0 8px 12px}
.langbar a{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:99px;
border:1px solid var(--line);color:var(--ink2);text-decoration:none}
.langbar a:hover{border-color:var(--blue);color:var(--blue)}
.versionbar{display:flex;align-items:center;justify-content:space-between;gap:8px;
padding:0 8px 12px;font-size:11.5px;color:var(--ink3)}
.versionbar .ver{background:var(--blue2);color:var(--blue);padding:2px 8px;border-radius:99px;
font-family:ui-monospace,Menlo,monospace}
.versionbar a{color:var(--blue);text-decoration:none}
.versionbar a:hover{text-decoration:underline}
.mobile-nav-toggle{display:none;width:100%;margin:0 0 10px;padding:9px 12px;border:1px solid var(--line);
border-radius:8px;background:#fff;color:var(--ink2);font:inherit;text-align:left;cursor:pointer}
.rolebar{display:flex;flex-wrap:wrap;gap:6px;padding:4px 8px 14px;border-bottom:1px solid var(--line);margin-bottom:12px}
.chip{font-size:12px;padding:3px 10px;border-radius:99px;border:1px solid var(--line);background:#fff;
color:var(--ink2);cursor:pointer;user-select:none}
.chip.on{background:var(--blue);border-color:var(--blue);color:#fff}
.searchbox{margin:0 8px 16px}
.searchbox input{width:100%;padding:7px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px;outline:none}
.searchbox input:focus{border-color:var(--blue)}
.navgroup{margin-bottom:14px}
.navgroup h4{font-size:11.5px;color:var(--ink3);letter-spacing:.08em;padding:0 8px 6px;font-weight:600}
.navitem{display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:8px;color:var(--ink2);
font-size:13px;text-decoration:none;line-height:1.4}
.navitem:hover{background:var(--blue2)}
.navitem .nid{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:var(--blue);
background:var(--blue2);padding:1px 6px;border-radius:4px;flex:0 0 auto}
.navitem .t{flex:1}
.navitem.hidden{display:none}
.navgroup.hidden{display:none}
/* 主区 */
.main{flex:1;min-width:0;padding:26px 34px 80px;max-width:920px}
.hero{margin-bottom:8px}
.hero h1{font-size:22px;margin-bottom:6px}
.hero p{color:var(--ink2);font-size:13.5px}
.stats{display:flex;gap:10px;margin:14px 0 6px;flex-wrap:wrap}
.stat{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:10px 16px}
.stat b{font-size:19px;display:block}.stat span{font-size:11.5px;color:var(--ink3)}
.quickgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0 24px}
.quickcard{display:block;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:14px 16px;text-decoration:none;color:var(--ink);transition:.16s ease}
.quickcard:hover{border-color:#b9cbe5;box-shadow:0 4px 14px rgba(37,65,99,.08);transform:translateY(-1px)}
.quickcard strong{display:block;font-size:14px;margin-bottom:5px}
.quickcard span{font-size:12px;color:var(--ink2)}
article{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:26px 30px;
margin:18px 0;scroll-margin-top:20px}
article.hidden{display:none}
.arthead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:4px}
.arthead .nid{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--blue);
background:var(--blue2);padding:2px 8px;border-radius:5px}
.arthead h2{font-size:18px}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 4px}
.badge{font-size:11px;padding:2px 9px;border-radius:99px;background:var(--blue2);color:var(--blue)}
.badge.adm{background:var(--amber2);color:var(--amber)}
.artsum{color:var(--ink2);font-size:13.5px;margin-bottom:12px}
.updated{font-size:11.5px;color:var(--ink3);text-align:right;margin-top:14px}
article h3{font-size:14.5px;margin:20px 0 8px;padding-left:10px;border-left:3px solid var(--blue)}
article h4{font-size:13.5px;margin:14px 0 6px;color:var(--ink2)}
article ol,article ul{padding-left:22px;margin:8px 0}
article li{margin:4px 0}
article table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
article th,article td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
article th{background:#f4f7fa;font-weight:600}
article blockquote.note{background:var(--amber2);border-left:3px solid var(--amber);
padding:9px 14px;border-radius:0 8px 8px 0;margin:10px 0;font-size:13px;color:#6b5518}
article code{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;background:#f1f5f8;
padding:1px 5px;border-radius:4px;color:#2c5480}
article img{max-width:100%;border:1px solid var(--line);border-radius:8px;margin:6px 0}
article a{color:var(--blue)}
.empty-tip{display:none;color:var(--ink3);font-size:13px;padding:30px;text-align:center}
/* 打印 */
@media print{
.sidebar{display:none}.main{padding:0;max-width:none}
article{border:none;page-break-inside:avoid;margin:14px 0}
body{background:#fff}
}
@media (max-width:900px){
.layout{display:block}
.sidebar{width:auto;position:static;height:auto;border-right:none;border-bottom:1px solid var(--line)}
.mobile-nav-toggle{display:block}
.navbody{display:none}.navbody.open{display:block}
.main{padding:18px 16px 60px;max-width:none}
}
"""

JS = """
(function(){
var chips=document.querySelectorAll('.chip[data-role]');
var items=document.querySelectorAll('.navitem[data-target]');
var arts=document.querySelectorAll('article[data-roles]');
var emptyTip=document.getElementById('empty-tip');
var navToggle=document.getElementById('mobile-nav-toggle');
var navBody=document.getElementById('nav-body');
var ALL=document.body.dataset.all;
var curRole=ALL, kw='';
function apply(){
  var visible=0;
  arts.forEach(function(a){
    var roles=(a.dataset.roles||'').trim().split(/\\s*\\|\\s*/);
    var okRole=(curRole===ALL)||roles.indexOf(curRole)>=0;
    var okKw=!kw||a.textContent.toLowerCase().indexOf(kw)>=0;
    var show=okRole&&okKw;
    a.classList.toggle('hidden',!show);
    if(show)visible++;
  });
  var navByTarget={};
  items.forEach(function(n){navByTarget[n.dataset.target]=n;});
  arts.forEach(function(a){
    var n=navByTarget[a.id];
    if(n)n.classList.toggle('hidden',a.classList.contains('hidden'));
  });
  document.querySelectorAll('.navgroup').forEach(function(g){
    var any=g.querySelector('.navitem:not(.hidden)');
    g.classList.toggle('hidden',!any);
  });
  document.querySelectorAll('.quickcard[data-quick-module]').forEach(function(card){
    var any=Array.prototype.some.call(arts,function(a){
      return a.dataset.module===card.dataset.quickModule && !a.classList.contains('hidden');
    });
    card.classList.toggle('hidden',!any);
  });
  emptyTip.style.display=visible?'none':'block';
}
chips.forEach(function(c){c.addEventListener('click',function(){
  chips.forEach(function(x){x.classList.remove('on')});
  c.classList.add('on');curRole=c.dataset.role;apply();
});});
document.getElementById('q').addEventListener('input',function(e){
  kw=e.target.value.trim().toLowerCase();apply();
});
if(navToggle&&navBody){navToggle.addEventListener('click',function(){
  var open=navBody.classList.toggle('open');
  navToggle.setAttribute('aria-expanded',open?'true':'false');
});}
apply();
})();
"""


def render(articles, lang, version_info=None, history_href=None, other_href=None):
    cfg = LANGS[lang]
    version_info = version_info or {
        "version": "unreleased",
        "label": "未发布" if lang == "zh" else "Unreleased",
        "released_at": "",
    }
    other = other_href or cfg["other"]
    history_href = history_href or ("versions/index.html" if lang == "zh" else "../versions/index.html")
    version_label = version_info.get("version", "unreleased")
    version_title = version_info.get("label", "")
    version_tip = cfg["version_tip"]
    if version_title:
        version_tip += f": {version_title}"
    mods = [m for m in cfg["mods"] if any(a["module"] == m for a in articles)]
    mods += [m for m in dict.fromkeys(a["module"] for a in articles) if m not in mods]
    articles = sorted(articles, key=lambda a: (mods.index(a["module"]), a["id"]))

    nav, arts = [], []
    for m in mods:
        nav.append(f'<div class="navgroup" data-module="{html.escape(m)}"><h4>{html.escape(m)}</h4>')
        for a in articles:
            if a["module"] != m:
                continue
            nav.append(
                f'<a class="navitem" data-target="{a["id"]}" href="#{a["id"]}">'
                f'<span class="nid">{a["id"]}</span><span class="t">{html.escape(a["title"])}</span></a>'
            )
        nav.append("</div>")

    admin_words = ("管理员", "超级管理员", "Admin", "Super Admin")
    for a in articles:
        badges = "".join(
            f'<span class="badge{" adm" if r in admin_words else ""}">{html.escape(r)}</span>'
            for r in a["roles"]
        )
        arts.append(
            f'<article id="{a["id"]}" data-roles="{html.escape("|".join(a["roles"]))}" data-module="{html.escape(a["module"])}">'
            f'<div class="arthead"><span class="nid">{a["id"]}</span><h2>{html.escape(a["title"])}</h2></div>'
            f'<div class="badges">{badges}</div>'
            f'<p class="artsum">{html.escape(a["summary"])}</p>'
            f'{a["html"]}'
            f'<p class="updated">{cfg["updated"]} {html.escape(a["updated"])}</p></article>'
        )

    chips = [f'<span class="chip on" data-role="{html.escape(cfg["chips"][0])}">{html.escape(cfg["chips"][0])}</span>']
    chips += [
        f'<span class="chip" data-role="{html.escape(r)}">{html.escape(r)}</span>' for r in cfg["chips"][1:]
    ]

    module_cards = []
    for module in mods:
        first = next(a for a in articles if a["module"] == module)
        count = sum(1 for a in articles if a["module"] == module)
        module_cards.append(
            f'<a class="quickcard" data-quick-module="{html.escape(module)}" href="#{first["id"]}">'
            f'<strong>{html.escape(module)}</strong><span>{count} {html.escape(cfg["stats"][0])}</span></a>'
        )

    page = f"""<!DOCTYPE html>
<html lang="{cfg["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(cfg["title"])}</title>
<link rel="alternate" hreflang="{'en' if lang == 'zh' else 'zh-CN'}" href="{html.escape(other)}">
<style>{CSS}</style>
</head>
<body data-all="{html.escape(cfg["chips"][0])}">
<div class="layout">
  <aside class="sidebar">
    <div class="brand"><b>{html.escape(cfg["brand"])}</b><span>{html.escape(cfg["brand_sub"])}</span></div>
    <div class="langbar"><a href="{html.escape(other)}" title="{html.escape(cfg["switch_title"])}">{html.escape(cfg["other_label"])}</a></div>
    <div class="versionbar"><span class="ver" title="{html.escape(version_tip)}">{html.escape(version_label)}</span><a href="{html.escape(history_href)}">{html.escape(cfg["history_label"])}</a></div>
    <button class="mobile-nav-toggle" id="mobile-nav-toggle" type="button" aria-controls="nav-body" aria-expanded="false">
      {'浏览目录' if lang == 'zh' else 'Browse guides'}
    </button>
    <div class="navbody" id="nav-body">
      <div class="rolebar">{''.join(chips)}</div>
      <div class="searchbox"><input id="q" type="search" placeholder="{html.escape(cfg["placeholder"])}"></div>
      {''.join(nav)}
    </div>
  </aside>
  <main class="main">
    <div class="hero">
      <h1>{html.escape(cfg["hero_h1"])}</h1>
      <p>{html.escape(cfg["hero_p"])}</p>
    </div>
    <div class="stats">
      <div class="stat"><b>{len(articles)}</b><span>{cfg["stats"][0]}</span></div>
      <div class="stat"><b>{len(mods)}</b><span>{cfg["stats"][1]}</span></div>
      <div class="stat"><b>{html.escape(version_label)}</b><span>{cfg["stats"][2]}</span></div>
    </div>
    <div class="quickgrid">{''.join(module_cards)}</div>
    <p class="empty-tip" id="empty-tip">{html.escape(cfg["empty"])}</p>
    {''.join(arts)}
  </main>
</div>
<script>{JS}</script>
</body>
</html>"""
    return page


def read_release_index():
    if not RELEASE_INDEX.exists():
        return {"current": None, "releases": []}
    data = json.loads(RELEASE_INDEX.read_text(encoding="utf-8"))
    data.setdefault("current", None)
    data.setdefault("releases", [])
    return data


def write_release_index(index):
    RELEASES.mkdir(parents=True, exist_ok=True)
    temp = RELEASE_INDEX.with_suffix(".json.tmp")
    temp.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(RELEASE_INDEX)


def latest_release(index):
    releases = index.get("releases", [])
    if not releases:
        return {
            "version": "unreleased",
            "label": "未发布",
            "summary": "当前内容尚未固化版本",
            "released_at": "",
            "changed_pages": [],
            "prd_urls": [],
        }
    return releases[0]


def article_manifest(built):
    return {
        lang: [
            {
                "id": article["id"],
                "title": article["title"],
                "module": article["module"],
                "updated": article["updated"],
                "summary": article["summary"],
                "content_hash": article["content_hash"],
                "src": article["src"],
            }
            for article in built[lang]
        ]
        for lang in ("zh", "en")
    }


def changed_articles(previous, current):
    old = {
        item["id"]: item.get("content_hash")
        for item in (previous or {}).get("zh", [])
    }
    changed = []
    for item in current.get("zh", []):
        if old.get(item["id"]) != item.get("content_hash"):
            changed.append(item["id"])
    changed.extend(sorted(set(old) - {item["id"] for item in current.get("zh", [])}))
    return changed


def check_bilingual(built):
    zh_ids = {a["id"] for a in built["zh"]}
    en_ids = {a["id"] for a in built["en"]}
    missing_en = sorted(zh_ids - en_ids)
    missing_zh = sorted(en_ids - zh_ids)
    if missing_en:
        print(f"  ! 缺少英文版: {', '.join(missing_en)}")
    if missing_zh:
        print(f"  ! 仅有英文版: {', '.join(missing_zh)}")
    return missing_en, missing_zh


def display_path(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def build_site_to(root, release_info, history_paths):
    root = Path(root)
    built = {}
    for lang in ("zh", "en"):
        print(f"收集文档（{lang}）…")
        articles = load_docs(lang, LANGS[lang]["img_prefix"])
        built[lang] = articles
        print(f"  共 {len(articles)} 篇：" + ", ".join(a["id"] for a in articles))
        out = root / LANGS[lang]["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        page = render(
            articles,
            lang,
            version_info=release_info,
            history_href=history_paths[lang],
        )
        out.write_text(page, encoding="utf-8")
        print(f"  → {display_path(out)} ({len(page.encode()) // 1024} KB)")

    check_bilingual(built)

    imgs = DOCS / "images"
    if imgs.exists():
        dst = root / "images"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(imgs, dst)
        print(f"  图片 → {display_path(dst)}")

    (root / ".nojekyll").write_text("", encoding="utf-8")
    return built


def create_release(args, index):
    version = args.release.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise SystemExit("版本号只能包含字母、数字、点、下划线和连字符。")
    final_root = RELEASES / version
    if final_root.exists():
        raise SystemExit(f"版本 {version} 已存在。历史版本不可覆盖，请使用新版本号。")

    previous_manifest = None
    if index["releases"]:
        previous_file = RELEASES / index["releases"][0]["version"] / "articles.json"
        if previous_file.exists():
            previous_manifest = json.loads(previous_file.read_text(encoding="utf-8"))

    RELEASES.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=f".{version}-", dir=RELEASES))
    site_root = temp_root / "site"
    release_info = {
        "version": version,
        "label": args.label or f"版本 {version}",
        "summary": args.summary or "",
        "released_at": args.released_at or date.today().isoformat(),
        "changed_pages": [],
        "prd_urls": args.prd_url or [],
    }
    built = build_site_to(
        site_root,
        release_info,
        {"zh": "../index.html", "en": "../../index.html"},
    )
    manifest = article_manifest(built)
    release_info["changed_pages"] = sorted(
        set(changed_articles(previous_manifest, manifest)) | set(args.changed_page or [])
    )

    (temp_root / "articles.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (temp_root / "release.json").write_text(
        json.dumps(release_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_root.replace(final_root)

    index["releases"].insert(0, release_info)
    index["current"] = version
    write_release_index(index)
    print(f"已固化历史版本 {version}（{release_info['released_at']}）")
    return index


VERSIONS_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2733;--ink2:#5b6b7c;--ink3:#8a97a6;--line:#e3e8ee;--blue:#2b5ca8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
main{max-width:960px;margin:0 auto;padding:40px 24px 72px}h1{font-size:26px;margin:0 0 6px}
.sub{color:var(--ink2);margin-bottom:24px}.card{background:var(--card);border:1px solid var(--line);
border-radius:12px;padding:20px;margin:14px 0}.head{display:flex;justify-content:space-between;
gap:16px;align-items:flex-start}.ver{font:600 16px ui-monospace,Menlo,monospace;color:var(--blue)}
.date{color:var(--ink3);font-size:12px}.label{font-weight:600;margin-top:4px}
.summary{color:var(--ink2);margin:8px 0}.links{display:flex;gap:16px;flex-wrap:wrap}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
.meta{color:var(--ink3);font-size:12px;margin-top:10px}.empty{color:var(--ink3);padding:32px 0}
"""


def versions_page(index):
    rows = []
    for release in index.get("releases", []):
        version = html.escape(release["version"])
        label = html.escape(release.get("label", ""))
        summary = html.escape(release.get("summary", ""))
        released_at = html.escape(release.get("released_at", ""))
        changed = html.escape("、".join(release.get("changed_pages", [])) or "—")
        prds = release.get("prd_urls", [])
        prd_links = " ".join(
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener">需求依据 {i + 1}</a>'
            for i, url in enumerate(prds)
        )
        rows.append(
            f'<section class="card"><div class="head"><div><div class="ver">v{version}</div>'
            f'<div class="label">{label}</div></div><div class="date">{released_at}</div></div>'
            f'<p class="summary">{summary}</p>'
            f'<div class="links"><a href="{version}/index.html">中文版本</a>'
            f'<a href="{version}/en/index.html">English</a>{prd_links}</div>'
            f'<div class="meta">变更页面：{changed}</div></section>'
        )
    if not rows:
        rows.append('<p class="empty">尚无已固化版本。执行带 --release 的构建后，历史版本会显示在这里。</p>')
    current = html.escape(index.get("current") or "unreleased")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dino CRM 手册版本历史</title><style>{VERSIONS_CSS}</style></head>
<body><main><h1>Dino CRM 手册版本历史</h1>
<p class="sub">当前版本：<strong>v{current}</strong>。所有版本按发布时间倒序，已发布快照不会覆盖。</p>
<p><a href="../index.html">返回当前手册</a> · <a href="../en/index.html">Current English handbook</a></p>
{''.join(rows)}</main></body></html>"""


def publish_versions(index):
    versions_dir = DIST / "versions"
    if versions_dir.exists():
        shutil.rmtree(versions_dir)
    versions_dir.mkdir(parents=True)
    for release in index.get("releases", []):
        src = RELEASES / release["version"]
        dst = versions_dir / release["version"]
        shutil.copytree(src / "site", dst)
        shutil.copy2(src / "release.json", dst / "release.json")
        shutil.copy2(src / "articles.json", dst / "articles.json")
    (versions_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (versions_dir / "index.html").write_text(versions_page(index), encoding="utf-8")
    print(f"  → {versions_dir.relative_to(ROOT)}/index.html（历史版本）")


def publish_current_from_release(release):
    source = RELEASES / release["version"] / "site"
    if not source.exists():
        raise SystemExit(f"版本 {release['version']} 的快照不存在，无法发布当前站点。")

    DIST.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "en", "images", ".nojekyll"):
        target = DIST / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    for name in ("index.html", "en", "images", ".nojekyll"):
        src = source / name
        dst = DIST / name
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.exists():
            shutil.copy2(src, dst)

    # 快照内的“历史版本”链接指向版本归档；固定入口需要改指向 versions/index.html。
    zh_index = DIST / "index.html"
    zh_text = zh_index.read_text(encoding="utf-8")
    zh_text = zh_text.replace(
        'href="../index.html">历史版本</a>',
        'href="versions/index.html">历史版本</a>',
    )
    zh_index.write_text(zh_text, encoding="utf-8")

    en_index = DIST / "en" / "index.html"
    en_text = en_index.read_text(encoding="utf-8")
    en_text = en_text.replace(
        'href="../../index.html">Version history</a>',
        'href="../versions/index.html">Version history</a>',
    )
    en_index.write_text(en_text, encoding="utf-8")
    print(f"已发布 v{release['version']} 到固定入口 dist/index.html")


def main():
    parser = argparse.ArgumentParser(description="构建 Dino CRM 双语使用手册")
    parser.add_argument("--release", help="固化并发布一个新的不可覆盖版本号")
    parser.add_argument("--check", action="store_true", help="只校验当前源稿，不更新当前站点")
    parser.add_argument("--label", default="", help="版本名称")
    parser.add_argument("--summary", default="", help="版本发布说明")
    parser.add_argument("--released-at", default="", help="发布日期 YYYY-MM-DD")
    parser.add_argument("--prd-url", action="append", default=[], help="关联 PRD，可重复传入")
    parser.add_argument(
        "--changed-page",
        action="append",
        default=[],
        help="强制标记变更的手册编号，可重复传入；脚本也会自动比对内容",
    )
    parser.add_argument("--list-releases", action="store_true", help="列出已固化版本")
    args = parser.parse_args()

    index = read_release_index()
    if args.list_releases:
        if not index["releases"]:
            print("尚无已固化版本。")
        for release in index["releases"]:
            print(
                f"v{release['version']}  {release.get('released_at', '')}  "
                f"{release.get('label', '')}  {release.get('summary', '')}"
            )
        return

    if args.release:
        index = create_release(args, index)

    if args.check:
        with tempfile.TemporaryDirectory(prefix="dino-crm-check-") as temp_dir:
            built = build_site_to(
                Path(temp_dir),
                {"version": "check", "label": "Source check"},
                {"zh": "versions/index.html", "en": "../versions/index.html"},
            )
        if {a["id"] for a in built["zh"]} != {a["id"] for a in built["en"]}:
            raise SystemExit("中英文手册编号不一致，检查失败。")
        print("源稿检查通过；当前站点未修改。")
        return

    if not index["releases"]:
        raise SystemExit("尚无已固化版本。请先使用 --release 建第一个版本。")

    current = index["releases"][0]
    publish_current_from_release(current)
    publish_versions(index)
    print(f"当前公开版本：v{current['version']}；固定入口未改变。")


if __name__ == "__main__":
    main()
