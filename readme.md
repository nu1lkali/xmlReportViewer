# XML 报告查看器

> 一个轻量级、拖拽式 Python 工具，用于直接查看带 XSL 样式的 XML 报告文件（如 ATML 格式）。

---

## 简介

**XML 报告查看器** 是一个基于 Python 的桌面应用，能够自动解析并渲染带有 XSL 样式表（XSLT）的 XML 文件。你只需将 `.xml` 文件拖入窗口，或通过"打开文件"按钮选择文件，即可在内嵌浏览器中实时查看格式化后的 HTML 报告。

该工具特别适用于：
- 查看测试报告（如 JUnit、TestNG、ATML 等生成的 XML）
- 浏览日志或结构化数据报告
- 快速调试 XSLT 样式转换效果
- 在现代浏览器无法渲染 XSL 的情况下替代旧版 IE 查看 XML 报告

---

## 功能特性

 **1、拖拽支持**：支持将 `.xml` 文件直接拖入窗口打开  
 **2、自动加载 XSL**：自动读取 XML 中的 `<?xml-stylesheet ...?>` 指令并应用样式  
 **3、内嵌 HTML 渲染**：使用 `tkinterweb.HtmlFrame` 实现本地 HTML 展示，无需外部浏览器  

---

## 背景：为什么需要这个工具？
**单位电脑升级了Windows10，但是很多远古工具会生成一个xml报告，但这个报告又不能在当前主流的浏览器中渲染。所以有了这个工具。**

**ATML（Automatic Test Markup Language）和许多工业级 XML 报告都基于标准 XML 格式。** 要将这些 XML 文件以可读的报告形式展示，必须应用相应的 **XSL 样式表（XSLT）** 进行转换。

历史上，**Internet Explorer（IE）** 是少数能在打开 XML 文件时自动应用 XSL 样式并渲染为 HTML 的浏览器之一。然而，**Chrome、Firefox、Edge（Chromium 版）等现代浏览器已不再支持在本地直接加载和应用 XSL 样式表**，导致许多遗留的 XML 报告无法正常查看。

### Internet Explorer 的组件说明

Internet Explorer 由两个主要部分组成：
- **IE Shell**：即用户界面（可执行文件），用于作为浏览器使用。
- **WebBrowser 控件（Trident 引擎）**：这是 IE 的核心渲染引擎，负责解析 HTML、XML 和应用 XSL 样式。

虽然 **IE Shell 已被微软正式弃用并停止支持**，但 **WebBrowser 控件（Trident）并未被完全淘汰**，仍在部分 Windows 应用中用于嵌入式网页渲染，并由 Microsoft 继续维护。

本工具利用现代 Python 库模拟了类似"WebBrowser 控件"的功能，在不依赖 IE 的前提下，实现对 XML + XSL 的本地渲染，帮助用户在 IE 退役后继续查看关键报告。

---

## 技术栈

- **Python 3.10**
- `lxml`：用于 XML/XSLT 解析与转换
- `tkinter`：构建图形界面
- `tkinterdnd2`：实现拖拽功能（支持跨平台）
- `tkinterweb`：嵌入式 HTML 渲染控件（模拟 WebBrowser 行为）
- `re` / `os` / `sys`：辅助文件处理与系统交互

---


![](https://img.erpweb.eu.org/imgs/2025/10/434d8514fea9597f.png)
