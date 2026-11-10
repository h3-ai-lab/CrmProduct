#!/usr/bin/env python3
"""Dino CRM 手册构建脚本（中英双语）。

用法:  python3 build.py
输入:  docs/**/*.md          （中文源）
       docs/en/**/*.md       （英文源）
输出:  dist/index.html       （中文站点）
       dist/en/index.html    （英文站点）
       dist/images/*         （截图，两站共用）
"""

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DIST = ROOT / "dist"
EN_DIR = "en"


# ---------- 多语言配置 ----------

LANGS = {
    "zh": {
        "scan": DOCS,
        "out": "index.html",
        "html_lang": "zh-CN",
        "img_prefix": "",
        "other": "en/",
        "other_label": "EN",
        "brand": "Dino CRM 手册",
        "brand_sub": "内部文档",
        "title": "Dino CRM 使用手册",
        "hero_h1": "Dino CRM 使用手册",
        "hero_p": "按任务和角色查找操作说明：一线伙伴跟着步骤做即可，管理员与超管的配置篇请切换角色筛选查看。",
        "placeholder": "搜索任务、功能或问题…",
        "chips": ["全部", "销售专员", "销售组长", "管理员", "超级管理员"],
        "stats": ["篇手册", "销售管理", "系统管理"],
        "updated": "最后更新",
        "empty": "当前筛选没有匹配的手册，换个角色或关键词试试。",
        "mods": ["管理看板", "销售管理", "营销中心", "用户与订单", "系统管理"],
        "count_mods": ["销售管理", "系统管理"],
        "switch_title": "Read in English",
    },
    "en": {
        "scan": DOCS / EN_DIR,
        "out": "en/index.html",
        "html_lang": "en",
        "img_prefix": "../",
        "other": "../",
        "other_label": "中文",
        "brand": "Dino CRM Handbook",
        "brand_sub": "Internal docs",
        "title": "Dino CRM Handbook",
        "hero_h1": "Dino CRM Handbook",
        "hero_p": "Find guidance by task and role. Frontline teams can follow the steps as written; admins and super admins can switch the role filter to see configuration guides.",
        "placeholder": "Search a task, feature or issue…",
        "chips": ["All", "Sales Rep", "Sales Lead", "Admin", "Super Admin"],
        "stats": ["guides", "Sales", "System Admin"],
        "updated": "Last updated",
        "empty": "No guides match the current filter. Try another role or a different keyword.",
        "mods": ["Dashboard", "Sales", "Marketing", "Users & Orders", "System Admin"],
        "count_mods": ["Sales", "System Admin"],
        "switch_title": "以中文阅读",
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

def load_docs(lang):
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
            "html": md_to_html(body, cfg["img_prefix"]),
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
.main{padding:18px 16px 60px;max-width:none}
}
"""

JS = """
(function(){
var chips=document.querySelectorAll('.chip[data-role]');
var items=document.querySelectorAll('.navitem[data-target]');
var arts=document.querySelectorAll('article[data-roles]');
var emptyTip=document.getElementById('empty-tip');
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
  emptyTip.style.display=visible?'none':'block';
}
chips.forEach(function(c){c.addEventListener('click',function(){
  chips.forEach(function(x){x.classList.remove('on')});
  c.classList.add('on');curRole=c.dataset.role;apply();
});});
document.getElementById('q').addEventListener('input',function(e){
  kw=e.target.value.trim().toLowerCase();apply();
});
apply();
})();
"""


def render(articles, lang):
    cfg = LANGS[lang]
    mods = [m for m in cfg["mods"] if any(a["module"] == m for a in articles)]
    mods += [m for m in dict.fromkeys(a["module"] for a in articles) if m not in mods]

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
            f'<article id="{a["id"]}" data-roles="{html.escape("|".join(a["roles"]))}">'
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

    m1, m2 = cfg["count_mods"]
    n1 = sum(1 for a in articles if a["module"] == m1)
    n2 = sum(1 for a in articles if a["module"] == m2)

    page = f"""<!DOCTYPE html>
<html lang="{cfg["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(cfg["title"])}</title>
<link rel="alternate" hreflang="{'en' if lang == 'zh' else 'zh-CN'}" href="{cfg["other"]}">
<style>{CSS}</style>
</head>
<body data-all="{html.escape(cfg["chips"][0])}">
<div class="layout">
  <aside class="sidebar">
    <div class="brand"><b>{html.escape(cfg["brand"])}</b><span>{html.escape(cfg["brand_sub"])}</span></div>
    <div class="langbar"><a href="{cfg["other"]}" title="{html.escape(cfg["switch_title"])}">{html.escape(cfg["other_label"])}</a></div>
    <div class="rolebar">{''.join(chips)}</div>
    <div class="searchbox"><input id="q" type="search" placeholder="{html.escape(cfg["placeholder"])}"></div>
    {''.join(nav)}
  </aside>
  <main class="main">
    <div class="hero">
      <h1>{html.escape(cfg["hero_h1"])}</h1>
      <p>{html.escape(cfg["hero_p"])}</p>
    </div>
    <div class="stats">
      <div class="stat"><b>{len(articles)}</b><span>{cfg["stats"][0]}</span></div>
      <div class="stat"><b>{n1}</b><span>{cfg["stats"][1]}</span></div>
      <div class="stat"><b>{n2}</b><span>{cfg["stats"][2]}</span></div>
    </div>
    <p class="empty-tip" id="empty-tip">{html.escape(cfg["empty"])}</p>
    {''.join(arts)}
  </main>
</div>
<script>{JS}</script>
</body>
</html>"""
    return page


def main():
    img_prefix_note = "截图共用 docs/images"

    built = {}
    for lang in ("zh", "en"):
        print(f"收集文档（{lang}）…")
        articles = load_docs(lang)
        print(f"  共 {len(articles)} 篇：" + ", ".join(a["id"] for a in articles))
        built[lang] = articles
        out = DIST / LANGS[lang]["out"]
        if not out.parent.exists():
            out.parent.mkdir(parents=True)
        page = render(articles, lang)
        out.write_text(page, encoding="utf-8")
        print(f"  → dist/{LANGS[lang]['out']} ({len(page.encode()) // 1024} KB)")

    # 双语一致性检查
    zh_ids = {a["id"] for a in built["zh"]}
    en_ids = {a["id"] for a in built["en"]}
    missing_en = sorted(zh_ids - en_ids)
    missing_zh = sorted(en_ids - zh_ids)
    if missing_en:
        print(f"  ! 缺少英文版: {', '.join(missing_en)}")
    if missing_zh:
        print(f"  ! 仅有英文版: {', '.join(missing_zh)}")

    imgs = DOCS / "images"
    if imgs.exists():
        dst = DIST / "images"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(imgs, dst)
        print(f"  图片 → dist/images ({img_prefix_note})")

    # GitHub Pages 需要 .nojekyll，避免下划线开头的资源被忽略
    if not (DIST / ".nojekyll").exists():
        (DIST / ".nojekyll").write_text("", encoding="utf-8")

    print("完成。")


if __name__ == "__main__":
    main()
