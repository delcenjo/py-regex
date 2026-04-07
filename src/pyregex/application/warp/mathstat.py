"""Warp Profiler — Curve Fitting Statistics.

Determines empirical Big-O complexity by calculating R-squared fits
for Linear, Quadratic, and Exponential models based on benchmark ticks.
"""

from __future__ import annotations
import math
from typing import List, Tuple

from pyregex.domain.warp.models import ComplexityCurve, IterationTick


class MathProfiler:
    """Statistical curve fitting engine."""

    def analyze_complexity(
        self, ticks: List[IterationTick]
    ) -> Tuple[ComplexityCurve, float]:
        """Returns the best fit curve type and its R-squared value."""
        if len(ticks) < 3:
            return ComplexityCurve.UNKNOWN, 0.0

        x_data = [t.input_length for t in ticks]
        y_data = [t.time_ms for t in ticks]

        # Guard against zero variances or completely flat lines
        if max(y_data) - min(y_data) < 0.01:
            return ComplexityCurve.CONSTANT, 1.0

        r2_linear = self._fit_linear(x_data, y_data)
        r2_quadratic = self._fit_quadratic(x_data, y_data)
        r2_exponential = self._fit_exponential(x_data, y_data)

        # Decision matrix based on highest R²
        best_fit = ComplexityCurve.UNKNOWN
        best_r2 = 0.0

        curves = [
            (r2_linear, ComplexityCurve.LINEAR),
            (r2_quadratic, ComplexityCurve.QUADRATIC),
            (r2_exponential, ComplexityCurve.EXPONENTIAL),
        ]

        for r2, curve in curves:
            if r2 > best_r2:
                best_r2 = r2
                best_fit = curve

        # If the highest R2 is still terrible, it's unpredictable
        if best_r2 < 0.5:
            return ComplexityCurve.UNKNOWN, best_r2

        return best_fit, best_r2

    def _fit_linear(self, x: List[int], y: List[float]) -> float:
        """y = mx + b"""
        try:
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_x2 = sum(xi**2 for xi in x)
            sum_xy = sum(x[i] * y[i] for i in range(n))

            denom = n * sum_x2 - sum_x**2
            if denom == 0:
                return 0.0

            m = (n * sum_xy - sum_x * sum_y) / denom
            b = (sum_y - m * sum_x) / n

            y_pred = [m * xi + b for xi in x]
            return self._calculate_r_squared(y, y_pred)
        except Exception:
            return 0.0

    def _fit_quadratic(self, x: List[int], y: List[float]) -> float:
        """Simplified heuristic fit: y = ax^2"""
        try:
            n = len(x)
            sum_x2 = sum(xi**2 for xi in x)
            sum_x4 = sum(xi**4 for xi in x)
            sum_x2y = sum((x[i] ** 2) * y[i] for i in range(n))

            if sum_x4 == 0:
                return 0.0

            a = sum_x2y / sum_x4
            y_pred = [a * (xi**2) for xi in x]

            return self._calculate_r_squared(y, y_pred)
        except Exception:
            return 0.0

    def _fit_exponential(self, x: List[int], y: List[float]) -> float:
        """Fit log(y) = mx + b  <=> y = e^b * e^(mx)"""
        try:
            MIN_Y = 0.0001
            # Filter valid points
            valid_x = []
            valid_ly = []
            for i in range(len(x)):
                if y[i] > MIN_Y:
                    valid_x.append(x[i])
                    valid_ly.append(math.log(y[i]))

            if len(valid_x) < 3:
                return 0.0

            n = len(valid_x)
            sum_x = sum(valid_x)
            sum_ly = sum(valid_ly)
            sum_x2 = sum(xi**2 for xi in valid_x)
            sum_xly = sum(valid_x[i] * valid_ly[i] for i in range(n))

            denom = n * sum_x2 - sum_x**2
            if denom == 0:
                return 0.0

            m = (n * sum_xly - sum_x * sum_ly) / denom
            b = (sum_ly - m * sum_x) / n

            A = math.exp(b)
            # Reconstruct y_pred using original bounds to prevent overflow
            y_pred = []
            for xi in x:
                exponent = m * xi
                if exponent > 500:  # clamp
                    y_pred.append(float("inf"))
                else:
                    y_pred.append(A * math.exp(exponent))

            return self._calculate_r_squared(y, y_pred)
        except Exception:
            return 0.0

    def _calculate_r_squared(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calculate the R^2 coefficient of determination."""
        try:
            mean_y = sum(y_true) / len(y_true)
            ss_tot = sum((yi - mean_y) ** 2 for yi in y_true)
            ss_res = sum(
                (y_true[i] - y_pred[i]) ** 2
                for i in range(len(y_true))
                if y_pred[i] != float("inf")
            )

            if ss_tot == 0:
                return 1.0
            r2 = 1 - (ss_res / ss_tot)
            return max(0.0, r2)
        except Exception:
            return 0.0
