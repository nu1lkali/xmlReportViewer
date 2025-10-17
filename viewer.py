import sys
import os
import re
from lxml import etree
from tkinter import Tk, Frame, Button, Label, messagebox, filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinterweb import HtmlFrame


def transform_xml_to_html(xml_path):
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_text = f.read()

        # 正则支持空格、大小写、单引号/双引号
        match = re.search(
            r'<\?xml-stylesheet\s+[^?]*?href\s*=\s*[\'"]([^\'"]+)[\'"][^?]*?\?>',
            xml_text,
            re.I | re.S
        )
        if not match:
            return """
            <div style="padding:20px; color:red; font-family:Arial;">
                <h3>❌ XML 未声明 XSL 样式表</h3>
                <p>请确保包含类似：</p>
                <pre>&lt;?xml-stylesheet type="text/xsl" href="your_style.xsl"?&gt;</pre>
            </div>
            """

        xsl_href = match.group(1).strip()
        xml_dir = os.path.dirname(os.path.abspath(xml_path))
        xsl_path = os.path.normpath(os.path.join(xml_dir, xsl_href))

        if not os.path.exists(xsl_path):
            return f"""
            <div style="padding:20px; color:red; font-family:Arial;">
                <h3>❌ 找不到 XSL 文件</h3>
                <p>查找路径：</p>
                <pre>{xsl_path}</pre>
                <p>声明的 href：</p>
                <pre>{xsl_href}</pre>
            </div>
            """

        # 执行 XSLT 转换
        xml_doc = etree.parse(xml_path)
        xsl_doc = etree.parse(xsl_path)
        transform = etree.XSLT(xsl_doc)
        result = transform(xml_doc)
        html = str(result)

        # 确保有基本结构
        if "<html" not in html:
            html = f"<html><body>{html}</body></html>"
        if "<head>" not in html:
            html = html.replace("<html>", '<html><head><meta charset="utf-8"></head>')

        return html

    except Exception as e:
        return f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:Arial;padding:20px;color:red;">
            <h3>❌ 转换失败</h3>
            <pre>{str(e)}</pre>
        </body>
        </html>
        """


# ========================
# 主窗口
# ========================

# 新增：全局函数 - 美化按钮
def style_button(button):
    """
    为 Tkinter 按钮应用现代化样式
    """
    button.config(
        bg='#5b9bd5',                    # 背景色 (蓝色调)
        fg='white',                      # 前景色 (白色文字)
        activebackground='#437cbb',      # 悬停时背景色
        activeforeground='white',        # 悬停时文字颜色
        relief='flat',                   # 扁平风格 (无边框)
        bd=0,                            # 边框宽度设为0
        padx=15,                         # 水平内边距
        pady=8,                          # 垂直内边距 (增加高度，解决"太扁"问题)
        font=("微软雅黑", 10, "bold"),   # 字体
        cursor='hand2'                   # 鼠标指针样式
    )

    # 添加鼠标悬停和离开的动态效果
    def on_enter(e):
        button['background'] = '#437cbb'
        button.config(relief='raised', bd=2)  # 模拟轻微凸起

    def on_leave(e):
        button['background'] = '#5b9bd5'
        button.config(relief='flat', bd=0)    # 恢复扁平

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)


class ReportViewer(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("XML 报告查看器 - 内置渲染")
        self.geometry("1000x700")
        self.minsize(600, 400)

        header = Frame(self)
        header.pack(fill="x", padx=10, pady=10)
        Label(header, text="XML 报告查看器", font=("微软雅黑", 14, "bold")).pack(side="left")
        Label(header, text=" | 拖入 .xml 文件即可查看", fg="gray").pack(side="left")

        # 使用 HtmlFrame，关闭调试消息
        self.html_frame = HtmlFrame(self, messages_enabled=False)
        self.html_frame.pack(fill="both", expand=True, padx=10, pady=5)

        footer = Frame(self)
        footer.pack(fill="x", padx=10, pady=10)

        # 创建按钮并应用美化样式
        # 打开文件
        btn_open = Button(footer, text="打开文件", command=self.load_file, width=12)
        style_button(btn_open)
        btn_open.pack(side="left", padx=5)

        # 返回首页
        btn_home = Button(footer, text="返回首页", command=self.show_welcome, width=12)
        style_button(btn_home)
        btn_home.pack(side="left", padx=5)

        # 退出
        btn_quit = Button(footer, text="退出", command=self.quit, width=12)
        style_button(btn_quit)
        btn_quit.pack(side="right", padx=5)

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

        self.show_welcome()

    def show_welcome(self):
        welcome_html = """
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family:Arial; padding:40px; text-align:center; color:#555;">
            <h2>欢迎使用 XML 报告查看器</h2>
            <p style="font-size:16px;">将 .xml 报告文件拖入此窗口，即可在内部直接查看</p>
            <p><br>支持自动加载 XSL 样式并渲染</p>
        </body>
        </html>
        """
        # 使用 load_html() 方法（v4+ 的正确 API）
        self.html_frame.load_html(welcome_html)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 XML 文件",
            filetypes=[("XML 文件", "*.xml")]
        )
        if file_path:
            self.display_report(file_path)

    def display_report(self, xml_path):
        html = transform_xml_to_html(xml_path)
        # 使用 load_html()
        self.html_frame.load_html(html)
        self.title(f"报告查看器 - {os.path.basename(xml_path)}")

    def on_drop(self, event):
        file_path = event.data.strip().strip("{}")
        if file_path.lower().endswith('.xml') and os.path.exists(file_path):
            self.display_report(file_path)
        else:
            messagebox.showwarning("提示", "请拖入有效的 .xml 文件")


def main():
    if len(sys.argv) > 1:
        xml_file = sys.argv[1]
        if os.path.isfile(xml_file) and xml_file.lower().endswith('.xml'):
            app = ReportViewer()
            app.display_report(xml_file)
            app.mainloop()
            return

    app = ReportViewer()
    app.mainloop()


if __name__ == '__main__':
    main()
