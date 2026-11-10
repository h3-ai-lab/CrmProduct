# Dino CRM 使用手册（中英双语 · 内部文档项目）

> 目标：CRM 每次功能迭代，手册同步更新、一条命令构建发布。
> 内容源 = `docs/`（中文）与 `docs/en/`（英文）下的 Markdown；构建产物 = 双站点：
> `dist/index.html`（中文）+ `dist/en/index.html`（英文），侧栏可互相切换语言。
> 功能：按模块分组导航、角色筛选（销售专员/组长、管理员/超管）、全文搜索、打印样式。

## 目录结构

```
crm-manual/
├── build.py              # 构建脚本（纯 Python 标准库，无需安装依赖）
├── .github/workflows/
│   └── deploy.yml        # push 到 main 自动构建并发布 GitHub Pages
├── docs/                 # ★ 中文内容源（只改这里）
│   ├── _template.md      # 新手册模板：复制 → 改名 → 填内容
│   ├── images/           # 截图统一放这里，构建时自动拷入 dist/images
│   ├── dashboard/        # 管理看板 D 系列
│   ├── sales/            # 销售管理 S-00~S-05（销售专员/组长）
│   ├── system/           # 系统管理 A-01~A-06（管理员/超管）
│   ├── marketing/        # 营销中心 M 系列
│   ├── user/             # 用户与订单 U/O 系列
│   └── en/               # ★ 英文内容源（与中文一一对应）
│       ├── sales/ system/ marketing/ user/ dashboard/
└── dist/                 # 构建产物（git 忽略，由 CI 生成）
    ├── index.html        # 中文站
    ├── en/index.html     # 英文站
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
3. **本地核对**：`python3 build.py`，打开 `dist/index.html` 与 `dist/en/index.html` 检查。
4. **提交并推送**：`git add docs/ && git commit -m "docs: ..."` → `git push`。CI 自动构建发布，约 1 分钟上线。

## 发布到 GitHub Pages（首次，约 5 分钟）

1. **建仓库**：在 GitHub 上新建仓库（如 `dino-crm-manual`），然后：

   ```bash
   cd crm-manual
   git init -b main
   git add -A
   git commit -m "feat: bilingual CRM manual, initial import"
   git remote add origin git@github.com:<你的用户名>/dino-crm-manual.git
   git push -u origin main
   ```

2. **开启 Pages**：仓库 **Settings → Pages → Build and deployment → Source 选 "GitHub Actions"**。
3. **完成**：之后每次 push 到 `main`，Action 自动构建并发布，地址为
   `https://<你的用户名>.github.io/dino-crm-manual/`（英文版在 `/en/` 后缀）。
   可在仓库 Actions 页查看构建日志；构建失败通常是中英篇数不一致（日志里有提示）。

> 私有仓库注意：GitHub **免费账户**的私有仓库不能使用 Pages；要么把仓库设为 Public（任何人拿到链接可看），要么升级 Pro/Team。见下方隐私清单。

## 发布前隐私检查清单 ⚠️

截图来自生产环境，其中**成员账号页与用户列表页含有员工邮箱和客户手机号**。对外发布前必须处理：

- [ ] `docs/images/` 中的敏感截图已打码（`A-01-members.png`、`U-01-userlist.png` 重点检查）
- [ ] 仓库可见性选择正确：Public = 任何人可看；Private 需付费版才能开 Pages
- [ ] 或改用内网部署：把 `dist/` 丢到公司内网任何静态服务器即可，无需 GitHub

## 规划中的角色与编号体系

| 角色 | 主要章节 | 说明 |
|---|---|---|
| Sales Rep / Sales Lead（销售专员 / 销售组长） | S 系列 | 跟单操作，纯执行视角 |
| Admin（管理员） | A 系列 + M 系列 | 业务配置：公海规则、通道账号、营销配置 |
| Super Admin（超级管理员） | A-01 / A-03 等授权项 | 权限、数据合规、审计 |
