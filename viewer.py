# viewer.py - XML 报告查看器 (修复 PyInstaller 路径问题)
import os
import sys
import re
import webview
from lxml import etree


# -----------------------------
# 工具函数：安全处理路径
# -----------------------------
def get_clean_path(path):
    if not path or not isinstance(path, str):
        return path
    # 去除引号
    path = path.strip()
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        path = path[1:-1].strip()
    if len(path) >= 2 and path.startswith("'") and path.endswith("'"):
        path = path[1:-1].strip()
    # 规范化路径
    return os.path.normpath(path)


# -----------------------------
# 启用 Windows 长路径 & UTF-8
# -----------------------------
if sys.platform == "win32":
    try:
        import ctypes
        # 启用长路径支持（>260 字符）
        ctypes.windll.kernel32.SetThreadErrorMode(0x0001)
        os.environ['PYTHONUTF8'] = '1'
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass


# -----------------------------
# XML -> HTML 转换
# -----------------------------
def transform_xml_to_html(xml_path):
    """将 XML + XSL 转换为 HTML"""
    try:
        xml_path = get_clean_path(xml_path)
        if not xml_path:
            return "<div style='color:red; padding:20px;'>❌ 无效文件路径</div>"

        print(f"[转换] 正在处理: {xml_path}")
        print(f"[转换] 文件存在? {os.path.exists(xml_path)}")
        print(f"[转换] 当前工作目录: {os.getcwd()}")

        if not os.path.exists(xml_path):
            return f"<div style='color:red; padding:20px;'>❌ 文件不存在: {xml_path}</div>"

        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_text = f.read()

        # 提取 XSL 引用
        match = re.search(
            r'<\?xml-stylesheet\s+[^?]*?href\s*=\s*[\'"]([^\'"]+)[\'"][^?]*?\?>',
            xml_text,
            re.I | re.S
        )
        if not match:
            return """
            <div style="padding:20px; color:red; font-family:Arial;">
                <h3>❌ XML 未声明 XSL 样式表</h3>
                <pre>&lt;?xml-stylesheet type="text/xsl" href="your_style.xsl"?&gt;</pre>
            </div>
            """

        xsl_href = match.group(1).strip()
        xml_dir = os.path.dirname(os.path.abspath(xml_path))
        xsl_path = os.path.normpath(os.path.join(xml_dir, xsl_href))

        if not os.path.exists(xsl_path):
            return f"""
            <div style="padding:20px; color:red;">
                <h3>❌ 找不到 XSL 文件</h3>
                <pre>{xsl_path}</pre>
            </div>
            """

        xml_doc = etree.parse(xml_path)
        xsl_doc = etree.parse(xsl_path)
        transform = etree.XSLT(xsl_doc)
        result = transform(xml_doc)
        return str(result)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[转换] 失败: {str(e)}\n{error_detail}")
        return f"<div style='color:red; font-family:Arial; padding:20px;'>❌ 转换失败: {str(e)}</div>"


# -----------------------------
# API 接口类
# -----------------------------
class API:
    def __init__(self):
        self.current_file = None  # 当前打开的文件路径

    def on_drop(self, data):
        """处理拖拽事件"""
        files = data.get('files', [])
        if not files:
            return {'error': 'No files'}

        file_path = files[0]
        print(f"[API] 收到拖拽文件: {file_path} (类型: {type(file_path)})")

        # 清理路径
        file_path = get_clean_path(file_path)
        if not file_path:
            return {'error': 'Invalid file path'}

        print(f"[API] 清理后路径: {file_path}")

        if not file_path.lower().endswith('.xml'):
            return {'error': 'Only .xml files'}

        if not os.path.exists(file_path):
            print(f"[API] 文件不存在: {file_path}")
            print(f"[API] 当前工作目录: {os.getcwd()}")
            return {'error': 'File not found'}

        html = transform_xml_to_html(file_path)
        self.current_file = file_path  # 设置当前文件

        return {
            'success': True,
            'html': html,
            'base_url': f'file:///{os.path.dirname(os.path.abspath(file_path)).replace(os.sep, "/")}/',
            'current_file': file_path
        }

    def refresh_current(self):
        """刷新当前文件"""
        if not self.current_file:
            return {'action': 'show_error', 'message': '没有文件可刷新'}

        clean_path = get_clean_path(self.current_file)
        if not os.path.exists(clean_path):
            return {'action': 'show_error', 'message': '文件已被删除或移动'}

        print(f"[API] 正在刷新: {clean_path}")
        html = transform_xml_to_html(clean_path)
        return {
            'action': 'update_content',
            'html': html,
            'current_file': clean_path
        }

    def go_home(self):
        """用户返回首页，清空当前文件状态"""
        print("[API] 用户返回首页")
        self.current_file = None
        return {'action': 'clear_content'}

    def exit_app(self):
        """退出应用"""
        print("[API] 收到退出请求")
        import threading
        threading.Thread(target=self._exit_soon, daemon=True).start()
        return None

    def _exit_soon(self):
        import time
        time.sleep(0.2)
        os._exit(0)

    def open_file_dialog(self):
        """打开文件对话框"""
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        file_path = filedialog.askopenfilename(
            title="选择 XML 文件",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        root.destroy()

        if not file_path:
            return {'error': 'No file selected'}

        file_path = get_clean_path(file_path)
        if not file_path.lower().endswith('.xml'):
            return {'error': 'Only .xml files'}

        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        html = transform_xml_to_html(file_path)
        self.current_file = file_path

        return {
            'success': True,
            'html': html,
            'base_url': f'file:///{os.path.dirname(os.path.abspath(file_path)).replace(os.sep, "/")}/',
            'current_file': file_path
        }


# -----------------------------
# 主函数
# -----------------------------
def main():
    api = API()

    # 首页内容
    HOME_CONTENT = """
        <div style="text-align:center; color:#888; padding:40px 0;">
            <h2>欢迎使用 XML 报告查看器</h2>
            <p>将 .xml 报告文件拖入此窗口</p>
            <p style="color:#888;">支持右键复制、全选、粘贴到 Excel</p>
        </div>
    """

    # 检查是否通过拖拽启动（拖文件到 .exe 上）
    auto_file = None
    if len(sys.argv) > 1:
        raw_path = sys.argv[1]
        print(f"[启动] 原始路径: {repr(raw_path)}")
        auto_file = get_clean_path(raw_path)
        print(f"[启动] 清理后路径: {auto_file}")

        if not os.path.exists(auto_file):
            print(f"[启动] ❌ 文件不存在: {auto_file}")
            auto_file = None
        elif not auto_file.lower().endswith('.xml'):
            print(f"[启动] ❌ 不是 XML 文件: {auto_file}")
            auto_file = None
    else:
        print("[启动] 无启动参数")

    initial_html = HOME_CONTENT
    auto_script = ""

    if auto_file:
        print(f"[启动] 自动加载文件: {auto_file}")
        html = transform_xml_to_html(auto_file)
        api.current_file = auto_file
        initial_html = html

        display_path = auto_file.replace('\\', '/')

        auto_script = f"""
        <script>
            setTimeout(() => {{
                document.getElementById('status').innerText = '当前文件: {display_path}';
            }}, 100);
        </script>
        """
    else:
        auto_script = ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>XML 查看器</title>
        <style>
            body {{
                font-family: Arial;
                margin: 0;
                padding: 40px;
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: #f5f5f5;
                transition: background 0.3s;
            }}
            #content {{
                flex: 1;
                overflow: auto;
                margin-top: 20px;
                border-top: 1px solid #ddd;
                padding-top: 20px;
            }}
            .controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                display: flex;
                gap: 8px;
            }}
            .controls button {{
                padding: 5px 10px;
                font-size: 12px;
            }}
            #status {{
                position: absolute;
                top: 10px;
                left: 10px;
                color: #666;
                font-size: 12px;
            }}
            #debug {{
                position: fixed;
                bottom: 10px;
                left: 10px;
                color: blue;
                font-size: 12px;
                z-index: 999;
            }}
            #content, #content * {{
                -webkit-user-select: text !important;
                -moz-user-select: text !important;
                -ms-user-select: text !important;
                user-select: text !important;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button onclick="refreshPage()">🔄 刷新</button>
            <button onclick="goHome()">🏠 首页</button>
            <button onclick="exitApp()">🚪 退出</button>
            <button onclick="openFile()">📂 打开 XML</button>
        </div>
        <div id="status"></div>
        <div id="content">
            {initial_html}
        </div>
        <div id="debug"></div>
        {auto_script}
    </body>
    <script>
        function debug(msg) {{
            document.getElementById('debug').innerText = msg;
            console.log('[DEBUG]', msg);
        }}

        window.addEventListener('pywebviewready', () => {{
            debug('pywebview API 已就绪');
        }});

        async function refreshPage() {{
            try {{
                const response = await window.pywebview.api.refresh_current();
                if (response.action === 'update_content') {{
                    document.getElementById('content').innerHTML = response.html;
                }} else if (response.message) {{
                    alert('操作失败: ' + response.message);
                }}
            }} catch (e) {{
                alert('刷新失败: ' + e.message);
            }}
        }}

        async function goHome() {{
            try {{
                await window.pywebview.api.go_home();
            }} catch (e) {{
                console.error('返回首页失败:', e);
            }}
            document.getElementById('content').innerHTML = `{HOME_CONTENT}`;
            document.getElementById('status').innerText = '';
        }}

        async function exitApp() {{
            if (confirm('确定退出？')) {{
                await window.pywebview.api.exit_app().catch(() => {{}});
            }}
        }}

        async function openFile() {{
            try {{
                const response = await window.pywebview.api.open_file_dialog();
                if (response.success) {{
                    document.getElementById('content').innerHTML = response.html;
                    document.getElementById('status').innerText = '当前文件: ' + response.current_file.replace(/\\\\/g, '/');
                }} else {{
                    alert('打开失败: ' + (response.error || '未知'));
                }}
            }} catch (e) {{
                alert('调用失败: ' + e.message);
            }}
        }}

        // 拖拽事件
        ['dragover', 'dragenter'].forEach(eventName => {{
            document.addEventListener(eventName, (e) => {{
                e.preventDefault();
                e.stopPropagation();
                document.body.style.background = '#e0f7fa';
            }}, false);
        }});

        document.addEventListener('dragleave', (e) => {{
            e.preventDefault();
            e.stopPropagation();
            document.body.style.background = '#f5f5f5';
        }}, false);

        document.addEventListener('drop', (e) => {{
            e.preventDefault();
            e.stopPropagation();
            document.body.style.background = '#f5f5f5';
            const files = Array.from(e.dataTransfer.files).map(f => f.path || f.name).filter(Boolean);
            if (files.length === 0) {{
                alert('无法读取文件路径');
                return;
            }}
            handleDrop(files);
        }}, false);

        async function handleDrop(files) {{
            try {{
                const response = await window.pywebview.api.on_drop({{files}});
                if (response.success) {{
                    document.getElementById('content').innerHTML = response.html;
                    document.getElementById('status').innerText = '当前文件: ' + response.current_file.replace(/\\\\/g, '/');
                }} else {{
                    document.getElementById('content').innerHTML = `<div style="color:red; padding:20px;">错误: ${{response.error}}</div>`;
                }}
            }} catch (err) {{
                console.error(err);
                document.getElementById('content').innerHTML = `<div style="color:red; padding:20px;">调用失败: ${{err.message}}</div>`;
            }}
        }}
    </script>
    </html>
    """

    window = webview.create_window(
        "XML 报告查看器",
        html=html_content,
        js_api=api,
        width=1000,
        height=700
    )

    # 使用 Edge Chromium
    webview.start(debug=False, gui='edgechromium')

    sys.exit(0)


if __name__ == '__main__':
    main()
