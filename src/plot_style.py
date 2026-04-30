from __future__ import annotations


def configure_chinese_font(plt) -> None:
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
