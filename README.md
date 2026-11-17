# Dino CRM 使用手册（中英双语 · 内部文档项目）

> 目标：CRM 每次功能迭代，手册同步更新、一条命令构建本地站点。
> 内容源 = `docs/`（中文）与 `docs/en/`（英文）下的 Markdown；构建产物 = 双站点：
> `dist/index.html`（中文）+ `dist/en/index.html`（英文），侧栏可互相切换语言。
> 功能：按模块分组导航、角色筛选（销售专员/组长、管理员/超管）、全文搜索、打印样式。

公网入口：`https://h3-ai-lab.github.io/CrmProduct/`

## 目录结构

```
crm-manual/
├── build.py              # 构建脚本（纯 Python 标准库，无需安装依赖）
├── .github/workflows/    # GitHub Pages 自动构建与部署
├── releases/             # 不可覆盖的版本快照和版本索引
├── docs/                 # ★ 中文内容源（只改这里）
│   ├── _template.md      # 新手册模板：复制 → 改名 → 填内容
│   ├── images/           # 截图统一放这里，构建时自动拷入 dist/images
│   ├── dashboard/        # 管理看板 D 系列
│   ├── start/            # 开始使用 G 系列
│   ├── sales/            # 销售管理 S-00~S-06（销售专员/组长）
│   ├── system/           # 系统管理 A-01~A-06（管理员/超管）
│   ├── marketing/        # 营销中心 M 系列
│   ├── user/             # 用户与订单 U/O 系列
│   └── en/               # ★ 英文内容源（与中文一一对应）
│       ├── start/ sales/ system/ marketing/ user/ dashboard/
└── dist/                 # 构建产物（git 忽略，由 build.py 生成）
    ├── index.html        # 中文站
    ├── en/index.html     # 英文站
    ├── versions/         # 历史版本
    └── images/           # 两站共用截图
```

## 双语怎么维护

- **中英一一对应**：`docs/sales/S-02.md` ↔ `docs/en/sales/S-02.md`，`id` 相同，结构、表格、图片完全一致。
- 英文版中，UI 元素首次出现时带中文原文，如 `Lead Pool (公海)`——方便在中文界面的系统里按图索骥。
- 构建时自动校验：中英篇数或 `id` 不一致会在构建日志中警告。
- 新增功能时，**中文和英文在同一批改动里一起加**（验收标准：手册已更新 = 两个语言版本都已更新）。

front-matter（两种语言字段一致，仅值不同）：

```yaml
---
id: S-02              # 编号（模块前缀 + 序号），也是页面锚点
title: 如何外呼并留下通话小结
module: 销售管理        # 中文版用中文模块名；英文版用 Sales / System Admin / Marketing / Users & Orders / Dashboard
roles: 销售专员, 管理员  # 英文版用 Sales Rep / Sales Lead / Admin / Super Admin
updated: 2026-11-10
summary: 一句话摘要
---
```

## 日常迭代工作流（功能更新 → 文档更新）

1. **开发功能时**：在 `docs/`（中文）和 `docs/en/`（英文）找到对应模块，新增或修改手册。编号体系：D 看板 / S 销售 / A 系统管理 / M 营销 / U 用户 / O 订单。
2. **功能验收标准包含一条：手册已更新**——没有手册的功能不算完成。
3. **源稿核对**：`python3 build.py --check`，确认中英文编号、转换和页面内容无误。该命令不会修改当前站点。
4. **需求上线后固化版本**：使用 `python3 build.py --release <version> ...`，更新固定入口并生成历史快照。
5. **提交到本地 Git**：同时提交 `docs/` 与 `releases/`，保留可追溯的本地版本历史。

## 版本与历史记录

当前 WorkBuddy 固定入口是：

`http://127.0.0.1:58078/preview/p1/index.html`

该地址始终展示 `dist/index.html`，不需要随版本变化。每次产品需求上线并完成手册更新后，使用：

```bash
python3 build.py --release 1.1.0 \
  --label "5.5 版本" \
  --released-at 2026-11-12 \
  --summary "本次上线内容" \
  --prd-url "https://example.com/prd"
```

每次发布会在 `releases/<version>/` 固化不可覆盖的快照，在 `dist/versions/` 生成历史版本页。侧栏的“历史版本”入口可查看各版本、发布日期、发布说明、变更页面和关联 PRD。

完整维护规范见 [MAINTENANCE.md](MAINTENANCE.md)。

## 发布

本地构建：

```bash
python3 build.py
```

推送到 `main` 后，GitHub Actions 会执行源稿检查、构建并发布到 GitHub Pages。

WorkBuddy 本地预览继续直接读取 `dist/`，本地入口保持不变。

## 发布前隐私检查清单 ⚠️

截图来自生产环境，其中**成员账号页与用户列表页含有员工邮箱和客户手机号**。对外发布前必须处理：

- [ ] `docs/images/` 中的敏感截图已打码（`A-01-members.png`、`U-01-userlist.png` 重点检查）
- [ ] 或改用内网部署：把 `dist/` 放入公司内网静态服务器

## 规划中的角色与编号体系

| 角色 | 主要章节 | 说明 |
|---|---|---|
| Sales Rep / Sales Lead（销售专员 / 销售组长） | S 系列 | 跟单操作，纯执行视角 |
| Admin（管理员） | A 系列 + M 系列 | 业务配置：公海规则、通道账号、营销配置 |
| Super Admin（超级管理员） | A-01 / A-03 等授权项 | 权限、数据合规、审计 |
