"""matplotlib 中文字体配置，保证 GUI 和报告图中的中文可显示。"""

from __future__ import annotations


def configure_chinese_font(plt) -> None:
    """从常见中文字体中选择一个已安装字体。"""
    try:
        import matplotlib.font_manager as fm
    except ImportError:
        return

    candidates = [
        "Arial Unicode MS",
        "PingFang SC",
        "Heiti SC",
        "Heiti TC",
        "Songti SC",
        "Noto Sans CJK SC",
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Zen Hei",
    ]
    installed = {font.name for font in fm.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return
