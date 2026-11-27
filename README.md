# 片刻 · Quiet Notes

wujunru 的个人博客。以 [Distill Blog Template](https://huggingface.co/spaces/lvwerra/distill-blog-template) 为基础，扩展为完整的中文个人博客。目标地址为 https://the-person-of-eat-icecream.github.io/。

包含首页、全文搜索、分类筛选、年份归档、关于页、独立文章链接、文章目录、阅读进度、原版 Distill 旁注和脚注、深浅色模式、RSS、站点地图和 404 页面。文章为构建时生成的 HTML，关闭 JavaScript 也可阅读。

## 本地预览

需要 Python 3.12 或更高版本。在此目录运行：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory dist --bind 127.0.0.1
```

打开 http://127.0.0.1:8000/。修改文件后重新运行构建脚本并刷新页面。

## 修改个人资料

编辑 `site.json` 中的博客名、英文名、作者、简介和关于页文字。`url` 为正式站点地址；GitHub Actions 发布时自动采用 Pages 返回的正式地址。

当前博客名和关于页是可修改的初始文案，三篇文章均为示例内容，不代表作者的真实经历。

## 写一篇新文章

在 `content/` 中添加 `my-first-post.md`。文件名只能包含小写英文字母、数字和连字符，它会变成永久链接 `/posts/my-first-post/`。

```markdown
---
title: 我的第一篇文章
date: 2026-11-27
category: 随笔
summary: 一句话介绍这篇文章。
featured: false
---

从这里开始写正文。

## 第一个小标题

支持 Markdown、代码块、链接、列表和 HTML。
```

把一篇文章的 `featured` 设为 `true`，即可显示在首页的置顶区域。若多篇置顶，优先展示日期最近的一篇。分类和归档自动生成。标题、日期、分类和摘要必填。使用 `##` 二级标题会自动生成文章目录。

旁注写法：`<aside>这是一条旁注。</aside>`。Distill 脚注写法：`正文<d-footnote>脚注内容。</d-footnote>`。

## 发布到 GitHub Pages

1. 在 **the-person-of-eat-icecream** 账户下创建名为 **the-person-of-eat-icecream.github.io** 的公开仓库。若已存在，先备份并确认如何整合，不能直接覆盖。
2. 将**本目录内部的源文件**上传到仓库的 `main` 分支，包含隐藏的 `.github/workflows/deploy.yml`，不包含 `.venv/` 和 `dist/`。不要把 `quiet-notes` 外层目录一起上传。
3. 在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
4. 在 **Actions → Build and deploy blog** 运行工作流，或向 `main` 推送新的提交。
5. 工作流成功后，访问 https://the-person-of-eat-icecream.github.io/。

之后新增或修改 Markdown 文章并推送到 `main`，网站会自动重新构建和部署。不需要付费服务器或数据库。此仓库使用 GitHub 提供的 Pages 工作流，仅部署生成的 `dist/`。

## 原模板许可

使用了原模板的 Distill 文章组件，保留了其原始版权和许可证。详见 `THIRD_PARTY_NOTICES.md` 和 `assets/vendor/LICENSE-2.0.txt`。
