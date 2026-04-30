from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from plot_style import configure_chinese_font


def plot_error_and_dop(
    times: Iterable[float],
    horiz: Iterable[float],
    three_d: Iterable[float],
    pdop: Iterable[float],
    save_path: Optional[str] = None,
    sat_counts: Optional[Iterable[int]] = None,
) -> bool:
    try:
        if save_path:
            import matplotlib

            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("未安装 matplotlib，已跳过绘图")
        return False
    configure_chinese_font(plt)

    time_list = list(times)
    horiz_list = list(horiz)
    three_d_list = list(three_d)
    pdop_list = list(pdop)
    sat_count_list = list(sat_counts) if sat_counts is not None else None
    if not time_list:
        print("没有可绘制的定位数据")
        return False

    row_count = 3 if sat_count_list is not None else 2
    fig, axes = plt.subplots(row_count, 1, figsize=(10, 3 * row_count), sharex=True)
    axes[0].plot(time_list, horiz_list, label="水平误差 (m)", linewidth=1.4)
    axes[0].plot(time_list, three_d_list, label="三维误差 (m)", linewidth=1.4)
    axes[0].set_ylabel("误差 (m)")
    axes[0].legend()
    axes[0].grid(True, linestyle="--", alpha=0.5)

    axes[1].plot(time_list, pdop_list, label="PDOP", linewidth=1.4)
    axes[1].set_xlabel("历元索引")
    axes[1].set_ylabel("DOP")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend()

    if sat_count_list is not None:
        axes[2].plot(time_list, sat_count_list, label="参与解算卫星数", linewidth=1.4)
        axes[2].set_xlabel("历元索引")
        axes[2].set_ylabel("卫星数")
        axes[2].grid(True, linestyle="--", alpha=0.5)
        axes[2].legend()

    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return Path(save_path).exists()
    else:
        plt.show()
        return True


def plot_trajectory(
    lat: Iterable[float],
    lon: Iterable[float],
    save_path: Optional[str] = None,
) -> bool:
    try:
        if save_path:
            import matplotlib

            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("未安装 matplotlib，已跳过绘图")
        return False
    configure_chinese_font(plt)

    lat_list = list(lat)
    lon_list = list(lon)
    if not lat_list or not lon_list:
        print("没有可绘制的轨迹数据")
        return False

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.scatter(lon_list, lat_list, s=12, alpha=0.75)
    ax.set_xlabel("经度 (deg)")
    ax.set_ylabel("纬度 (deg)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")

    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return Path(save_path).exists()
    else:
        plt.show()
        return True


def playback_trajectory(
    lat: Iterable[float],
    lon: Iterable[float],
    interval_ms: int = 100,
) -> Optional[object]:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except ImportError:
        print("未安装 matplotlib，已跳过轨迹回放")
        return None
    configure_chinese_font(plt)

    lat_list = list(lat)
    lon_list = list(lon)
    if not lat_list or not lon_list:
        print("没有可回放的轨迹数据")
        return None

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.set_xlabel("经度 (deg)")
    ax.set_ylabel("纬度 (deg)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")

    history = ax.scatter([], [], s=10, alpha=0.45)
    point = ax.scatter([], [], s=28)

    def init() -> tuple:
        min_lon = min(lon_list)
        max_lon = max(lon_list)
        min_lat = min(lat_list)
        max_lat = max(lat_list)
        if min_lon == max_lon:
            min_lon -= 1e-5
            max_lon += 1e-5
        if min_lat == max_lat:
            min_lat -= 1e-5
            max_lat += 1e-5
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        history.set_offsets([(float("nan"), float("nan"))])
        point.set_offsets([(float("nan"), float("nan"))])
        return history, point

    def update(frame: int) -> tuple:
        history.set_offsets(list(zip(lon_list[: frame + 1], lat_list[: frame + 1])))
        point.set_offsets([(lon_list[frame], lat_list[frame])])
        return history, point

    anim = FuncAnimation(fig, update, frames=len(lat_list), init_func=init, interval=interval_ms, blit=True)
    plt.show()
    return anim
