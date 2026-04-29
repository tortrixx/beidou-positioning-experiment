from __future__ import annotations

from typing import Iterable, Optional


def plot_error_and_dop(
    times: Iterable[float],
    horiz: Iterable[float],
    three_d: Iterable[float],
    pdop: Iterable[float],
    save_path: Optional[str] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skip plotting")
        return

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(list(times), list(horiz), label="Horizontal error (m)")
    axes[0].plot(list(times), list(three_d), label="3D error (m)")
    axes[0].set_ylabel("Error (m)")
    axes[0].legend()
    axes[0].grid(True, linestyle="--", alpha=0.5)

    axes[1].plot(list(times), list(pdop), label="PDOP")
    axes[1].set_xlabel("Epoch index")
    axes[1].set_ylabel("DOP")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend()

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()


def plot_trajectory(
    lat: Iterable[float],
    lon: Iterable[float],
    save_path: Optional[str] = None,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skip plotting")
        return

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.plot(list(lon), list(lat), linewidth=1.0)
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()


def playback_trajectory(
    lat: Iterable[float],
    lon: Iterable[float],
    interval_ms: int = 100,
) -> Optional[object]:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except ImportError:
        print("matplotlib not available; skip playback")
        return None

    lat_list = list(lat)
    lon_list = list(lon)
    if not lat_list or not lon_list:
        print("No trajectory data")
        return None

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")

    line, = ax.plot([], [], linewidth=1.0)
    point, = ax.plot([], [], marker="o", markersize=4)

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
        line.set_data([], [])
        point.set_data([], [])
        return line, point

    def update(frame: int) -> tuple:
        line.set_data(lon_list[: frame + 1], lat_list[: frame + 1])
        point.set_data(lon_list[frame], lat_list[frame])
        return line, point

    anim = FuncAnimation(fig, update, frames=len(lat_list), init_func=init, interval=interval_ms, blit=True)
    plt.show()
    return anim
