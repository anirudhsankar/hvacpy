"""PsychChart — matplotlib-based SI psychrometric chart.

Renders constant RH curves, and allows plotting AirState points
and AirProcess arrows on a psychrometric chart.

No psychrometric equations in this module — it calls _equations.py
for all curve data generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless use.
import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np

from hvacpy.psychrometrics import _equations as _eq
from hvacpy.psychrometrics._equations import P_STD_PA

if TYPE_CHECKING:
    from hvacpy.psychrometrics import AirState
    from hvacpy.psychrometrics._process import AirProcess


class PsychChart:
    """Interactive SI psychrometric chart.

    Renders constant RH curves on a dry-bulb vs humidity-ratio plot
    and allows adding state points and process arrows.

    Args:
        t_range: Tuple of (min, max) dry bulb temperature in °C.
            Default (-10, 50).
        p_pa: Atmospheric pressure in Pa. Default 101325.
    """

    def __init__(
        self,
        t_range: tuple[float, float] = (-10.0, 50.0),
        p_pa: float = P_STD_PA,
    ) -> None:
        self._t_min = t_range[0]
        self._t_max = t_range[1]
        self._p_pa = p_pa
        self._points: list[dict] = []
        self._processes: list[dict] = []

    def add_point(
        self,
        label: str,
        state: "AirState",
        color: str = "blue",
        marker: str = "o",
    ) -> "PsychChart":
        """Add an AirState point to the chart.

        Args:
            label: Text label for the point.
            state: AirState instance to plot.
            color: Marker color. Default 'blue'.
            marker: Marker style. Default 'o'.

        Returns:
            self, enabling method chaining.
        """
        self._points.append({
            "label": label,
            "t_db": state._t_db,
            "W_gkg": state._W * 1000.0,
            "color": color,
            "marker": marker,
        })
        return self

    def add_process(
        self,
        process: "AirProcess",
        label: str = "",
        color: str = "red",
    ) -> "PsychChart":
        """Add an AirProcess arrow to the chart.

        Args:
            process: AirProcess instance to plot.
            label: Optional text label for the process.
            color: Arrow color. Default 'red'.

        Returns:
            self, enabling method chaining.
        """
        self._processes.append({
            "label": label,
            "t_db_in": process._t_db_in,
            "W_gkg_in": process._W_in * 1000.0,
            "t_db_out": process._t_db_out,
            "W_gkg_out": process._W_out * 1000.0,
            "color": color,
        })
        return self

    def plot(
        self, figsize: tuple[int, int] = (12, 8)
    ) -> matplotlib.figure.Figure:
        """Render the psychrometric chart.

        Args:
            figsize: Figure size as (width, height) in inches.

        Returns:
            matplotlib Figure instance.
        """
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Generate temperature array for curves.
        t_arr = np.linspace(self._t_min, self._t_max, 300)

        # ── Constant RH curves ──────────────────────────────────
        rh_levels = [0.10, 0.20, 0.30, 0.40, 0.50,
                     0.60, 0.70, 0.80, 0.90, 1.00]

        for rh_val in rh_levels:
            W_arr = np.array([
                _eq.humidity_ratio_from_rh(t, rh_val, self._p_pa)
                for t in t_arr
            ])
            W_gkg = W_arr * 1000.0

            # Saturation line (100% RH) is thicker and blue.
            if rh_val == 1.0:
                ax.plot(
                    t_arr, W_gkg,
                    color="steelblue", linewidth=2.0,
                    label="100% RH",
                )
            else:
                ax.plot(
                    t_arr, W_gkg,
                    color="grey", linewidth=0.7, alpha=0.6,
                )

            # Label at right edge.
            try:
                W_label = _eq.humidity_ratio_from_rh(
                    self._t_max, rh_val, self._p_pa
                )
                ax.text(
                    self._t_max + 0.5, W_label * 1000.0,
                    f"{int(rh_val * 100)}%",
                    fontsize=7, color="grey",
                    verticalalignment="center",
                )
            except Exception:
                pass

        # ── State points ────────────────────────────────────────
        for pt in self._points:
            ax.plot(
                pt["t_db"], pt["W_gkg"],
                marker=pt["marker"],
                color=pt["color"],
                markersize=8,
                zorder=5,
            )
            ax.annotate(
                pt["label"],
                (pt["t_db"], pt["W_gkg"]),
                textcoords="offset points",
                xytext=(8, 8),
                fontsize=9,
                color=pt["color"],
                fontweight="bold",
            )

        # ── Process arrows ──────────────────────────────────────
        for proc in self._processes:
            ax.annotate(
                proc["label"],
                xy=(proc["t_db_out"], proc["W_gkg_out"]),
                xytext=(proc["t_db_in"], proc["W_gkg_in"]),
                arrowprops=dict(
                    arrowstyle="->",
                    color=proc["color"],
                    lw=1.5,
                ),
                fontsize=8,
                color=proc["color"],
            )

        # ── Formatting ──────────────────────────────────────────
        ax.set_xlabel("Dry Bulb Temperature (°C)", fontsize=11)
        ax.set_ylabel("Humidity Ratio (g/kg)", fontsize=11)
        ax.set_title(
            f"Psychrometric Chart — {int(round(self._p_pa))} Pa",
            fontsize=13,
        )
        ax.set_xlim(self._t_min, self._t_max + 3)
        ax.grid(True, color="lightgrey", alpha=0.3)
        ax.set_ylim(bottom=0)

        fig.tight_layout()
        return fig

    def save(self, path: str, dpi: int = 150) -> None:
        """Save the chart to a file.

        Args:
            path: File path for the output image.
            dpi: Resolution in dots per inch. Default 150.
        """
        fig = self.plot()
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
