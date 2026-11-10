# 使用手册版本维护流程

## 固定入口

对外地址保持不变：

`http://127.0.0.1:58078/preview/p1/index.html`

WorkBuddy 将 `/preview/p1/` 映射到 `crm-manual/dist/`，服务会实时读取文件。更新手册只需重建 `dist/`，不要修改端口、预览 token 或入口路径。

当前不维护任何 GitHub、GitLab 或其他远端发布流程。

## 每次需求上线

收到“需求已上线”通知后：

1. 读取对应 PRD、上线说明和截图。
2. 核对线上实际行为，区分已上线、灰度中和计划中能力。
3. 使用 `audit/route-manifest.json` 定位受影响的现有手册。
4. 同时更新中文 `docs/` 和英文 `docs/en/`。
5. 执行源稿检查，确认页面、角色筛选、搜索、图片和语言切换。
6. 确认版本号、发布日期、发布说明和 PRD 链接。
7. 固化版本并发布到当前地址。
8. 验证当前版本、英文版本、历史索引和本版本归档都可访问。

## 发布命令

```bash
cd crm-manual

python3 build.py --check

python3 build.py --release 1.1.0 \
  --label "5.5 版本" \
  --released-at 2026-11-12 \
  --summary "新增短链管理、TikTok Leads、Messenger 来源区分、五类学习报告和用户导出扩容。" \
  --prd-url "https://example.com/prd" \
  --changed-page M-01 \
  --changed-page S-00
```

脚本会：

- 自动比对上一版本内容并记录发生变化的页面。
- 同时写入 `--changed-page` 指定的页面。
- 生成不可覆盖的 `releases/<version>/site/` 快照。
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
- [ ] 旧版本内容仍可访问且没有被覆盖。
- [ ] 固定入口 `/preview/p1/index.html` 可访问。
- [ ] 构建脚本无报错，中英文文档编号一致。

