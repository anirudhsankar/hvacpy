"""Chart rendering smoke tests — Tests P-E01 through P-E03.

No pixel comparison — only verifies that chart creation, point
addition, and rendering complete without error.
"""

import matplotlib.figure
import pytest

from hvacpy import Q_, AirState
from hvacpy.psychrometrics import PsychChart, AirProcess


class TestGroupE:
    """Tests P-E01 through P-E03 — PsychChart smoke tests."""

    def test_pe01_instantiation(self) -> None:
        """P-E01: PsychChart instantiates without error."""
        chart = PsychChart()
        assert isinstance(chart, PsychChart)

    def test_pe02_add_point_and_plot(self) -> None:
        """P-E02: add_point and plot return without error."""
        chart = PsychChart()
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        chart.add_point("Office", s)
        fig = chart.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_pe03_method_chaining(self) -> None:
        """P-E03: Method chaining works."""
        s1 = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        s2 = AirState(dry_bulb=Q_(13, "degC"), rh=0.95)
        fig = (
            PsychChart()
            .add_point("A", s1)
            .add_point("B", s2)
            .plot()
        )
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_add_process(self) -> None:
        """Process arrows render without error."""
        s_in = AirState(dry_bulb=Q_(28, "degC"), rh=0.65)
        s_out = AirState(dry_bulb=Q_(13, "degC"), rh=0.95)
        proc = AirProcess(s_in, s_out, Q_(1, "kg/s"))
        chart = PsychChart()
        chart.add_point("In", s_in)
        chart.add_point("Out", s_out)
        chart.add_process(proc, label="Cooling")
        fig = chart.plot()
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_save(self, tmp_path) -> None:
        """save() writes a file without error."""
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        chart = PsychChart()
        chart.add_point("Test", s)
        path = str(tmp_path / "test_chart.png")
        chart.save(path)
        import os
        assert os.path.exists(path)
