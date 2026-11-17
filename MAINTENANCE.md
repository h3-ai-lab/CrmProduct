# 使用手册版本维护流程

## 固定入口

对外地址保持不变：

`http://127.0.0.1:58078/preview/p1/index.html`

WorkBuddy 将 `/preview/p1/` 映射到 `crm-manual/dist/`，服务会实时读取文件。更新手册只需重建 `dist/`，不要修改端口、预览 token 或入口路径。

公网发布使用 GitHub Pages：

- 仓库：`h3-ai-lab/CrmProduct`
- 地址：`https://h3-ai-lab.github.io/CrmProduct/`
- 推送 `main` 后由 `.github/workflows/pages.yml` 自动构建和部署。

## 每次需求上线

收到“需求已上线”通知后：

触发语可能是“`xxx需求已上线`”，需求可能来自另一个聊天窗口。

1. 在 `crm-prd/projects/` 中定位对应 PRD；找不到时使用用户提供的 PRD 链接。
2. 读取 PRD、上线说明、截图和当前中英文手册。
3. 核对线上实际行为，区分已上线、灰度中和计划中能力。
4. 定位受影响的手册编号、页面和截图。
5. 同时更新中文 `docs/` 和英文 `docs/en/`。
6. UI 有变化时更新截图，并处理生产数据和个人信息。
7. 执行 `python3 build.py --check`。
8. 确认新版本号、发布日期、发布说明和 PRD 链接。
9. 固化新版本并重建 `dist/`。
10. 检查自动生成的 `CHANGELOG.md` 和历史版本页中的模块变化。
11. 提交并推送到 GitHub `main`。
12. 等待 `Deploy CrmProduct` 部署完成。
13. 验证公网中文、英文、版本更新记录和本版本归档。

## 发布命令

```bash
cd crm-manual

python3 build.py --check

python3 build.py --release 1.1.0 \
  --label "5.5 版本" \
  --released-at 2026-11-12 \
  --summary "新增短链管理、TikTok Leads、Messenger 来源区分、五类学习报告和用户导出扩容。" \
  --prd-url "https://example.com/prd" \
  --requirement "REQ-XXX-001" \
  --change "营销中心：新增短链管理" \
  --change "销售中心：接入 TikTok Leads" \
  --changed-page M-01 \
  --changed-page S-00
```

脚本会：

- 自动比对上一版本内容并记录发生变化的页面。
- 同时写入 `--changed-page` 指定的页面。
- 生成不可覆盖的 `releases/<version>/site/` 快照。
- 生成 `CHANGELOG.md`，记录版本、日期、需求编号、变更模块和页面。
- 在历史版本页列出变更模块和对应页面。
- 更新 `releases/index.json`。
- 重建当前站点和 `dist/versions/index.html`。
- 保持 `/preview/p1/index.html` 继续指向最新版本。

普通构建不会创建新版本：

```bash
python3 build.py
```

普通构建只重新发布最新的已固化版本，不会把未发布的源稿推到当前地址；编辑中的内容使用 `--check` 校验。

查看版本：

```bash
python3 build.py --list-releases
```

## 输出结构

```text
crm-manual/
├── docs/                      当前中文源
├── docs/en/                   当前英文源
├── releases/
│   ├── index.json             版本索引
│   └── <version>/
│       ├── release.json       发布信息、PRD、变更页面
│       ├── articles.json      各篇内容哈希
│       └── site/              不可覆盖的静态快照
└── dist/
    ├── index.html             当前中文版（固定入口）
    ├── en/index.html          当前英文版
    └── versions/
        ├── index.html         历史版本页面
        └── <version>/         历史快照
```

## 验收清单

- [ ] 中英文对应页面都已更新。
- [ ] 手册描述与线上实际行为一致。
- [ ] 所有截图来自当前上线版本，敏感信息已处理。
- [ ] 当前页面显示正确版本号。
- [ ] 历史版本页包含发布日期、发布说明、变更页面和 PRD 链接。
- [ ] `CHANGELOG.md` 已更新，变更模块和页面与实际修改一致。
- [ ] 旧版本内容仍可访问且没有被覆盖。
- [ ] 固定入口 `/preview/p1/index.html` 可访问。
- [ ] 构建脚本无报错，中英文文档编号一致。
- [ ] GitHub Pages 最新部署成功，公网中英文和历史版本返回正常。

