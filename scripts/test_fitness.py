import math

import pytest

from fitness import classify_attractor, converged, fitness


class TestFitness:
    @pytest.mark.parametrize("n", [1, 5, 15, 27, 40, 65])
    def test_all_tens_is_one(self, n):
        # The normalizer is 10*sqrt(N): a perfect vector scores exactly 1.0 for any N.
        assert fitness([10] * n) == pytest.approx(1.0)

    @pytest.mark.parametrize("n", [1, 5, 27])
    def test_all_zeros_is_zero(self, n):
        assert fitness([0] * n) == pytest.approx(0.0)

    def test_rms_rewards_spike_over_uniform(self):
        # L2/RMS deliberately scores spiky excellence above uniform mediocrity.
        assert fitness([10, 10, 10, 0, 0]) == pytest.approx(
            math.sqrt(300) / (10 * math.sqrt(5))
        )
        assert fitness([10, 10, 10, 0, 0]) == pytest.approx(0.7745966, abs=1e-6)
        assert fitness([6, 6, 6, 6, 6]) == pytest.approx(0.6)
        assert fitness([10, 10, 10, 0, 0]) > fitness([6, 6, 6, 6, 6])

    def test_single_criterion(self):
        assert fitness([7]) == pytest.approx(0.7)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            fitness([])

    @pytest.mark.parametrize("bad", [[-1], [11], [5, 10.5], [5, -0.1]])
    def test_out_of_range_raises(self, bad):
        with pytest.raises(ValueError):
            fitness(bad)


class TestConverged:
    def test_hard_target(self):
        assert converged([0.5, 0.96]) is True

    def test_asymptote_in_band(self):
        assert converged([0.80, 0.86, 0.862, 0.861]) is True

    def test_below_band_flat_not_converged(self):
        assert converged([0.60, 0.605, 0.602]) is False

    def test_still_climbing_not_converged(self):
        assert converged([0.5, 0.6, 0.7]) is False


class TestClassifyAttractor:
    def test_converged_hard(self):
        r = classify_attractor([0.5, 0.96])
        assert r["label"] == "converged"
        assert r["action"] == "stop"

    def test_converged_asymptotic(self):
        r = classify_attractor([0.80, 0.86, 0.862, 0.861])
        assert r["label"] == "converged"
        assert r["action"] == "stop"

    def test_converging(self):
        r = classify_attractor([0.4, 0.55, 0.7, 0.83])
        assert r["label"] == "converging"
        assert r["action"] == "continue"

    def test_diverging(self):
        r = classify_attractor([0.8, 0.7, 0.6, 0.5])
        assert r["label"] == "diverging"
        assert r["action"] == "restart"

    def test_cyclic(self):
        r = classify_attractor([0.6, 0.75, 0.6, 0.75, 0.6])
        assert r["label"] == "cyclic"
        assert r["action"] == "restart"

    def test_strange(self):
        r = classify_attractor([0.4, 0.85, 0.55, 0.9, 0.3])
        assert r["label"] == "strange"
        assert r["action"] == "restart"

    def test_stuck_low(self):
        r = classify_attractor([0.62, 0.625, 0.62, 0.622, 0.621])
        assert r["label"] == "stuck_low"
        assert r["action"] == "restart"

    def test_warming_up_single_point(self):
        assert classify_attractor([0.5])["action"] == "continue"

    def test_empty_history(self):
        assert classify_attractor([])["action"] == "continue"
