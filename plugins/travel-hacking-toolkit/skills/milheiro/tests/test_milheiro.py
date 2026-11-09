#!/usr/bin/env python3
"""Unit tests for the milheiro calculator.

No network, no live prices, no club defaults. Illustrative numbers only.

Run:
    python3 -m unittest discover -s skills/milheiro/tests
    python3 -m pytest skills/milheiro/tests
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.join(_HERE, "..", "scripts", "calc_milheiro.py")
_spec = importlib.util.spec_from_file_location("calc_milheiro", _SCRIPT)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


class FormulaTests(unittest.TestCase):
    def test_basic_custo(self):
        # R$ 200 for 10_000 miles → R$ 20 / 1.000
        self.assertAlmostEqual(m.custo_milheiro(200, 10_000), 20.0)

    def test_eighty_percent_bonus(self):
        # R$ 270 for 10_000 + 80% → 18_000 miles → R$ 15
        credited = m.miles_credited(10_000, bonus_pct=80)
        self.assertAlmostEqual(credited, 18_000)
        self.assertAlmostEqual(m.custo_milheiro(270, credited), 15.0)

    def test_additive_club_stack_is_default_br_banner_math(self):
        # 80% promo + 30% clube = 110% → 21_000 miles on 10_000 base
        credited = m.miles_credited(10_000, 80, 30, "additive")
        self.assertAlmostEqual(credited, 21_000)
        out = m.purchase_milheiro(270, 10_000, 80, 30, "additive")
        self.assertAlmostEqual(out["custo_milheiro"], round(270 * 1000 / 21_000, 4))
        self.assertEqual(out["bonus_mode"], "additive")

    def test_multiplicative_differs_from_additive(self):
        add = m.miles_credited(10_000, 80, 30, "additive")
        mul = m.miles_credited(10_000, 80, 30, "multiplicative")
        self.assertAlmostEqual(add, 21_000)
        self.assertAlmostEqual(mul, 10_000 * 1.8 * 1.3)
        self.assertGreater(mul, add)

    def test_transfer_100_percent_bonus_halves_milheiro(self):
        # Livelo milheiro R$ 14, 1:1, +100% → Smiles milheiro R$ 7
        out = m.transfer_milheiro(source_milheiro=14, ratio=1.0, bonus_pct=100)
        self.assertAlmostEqual(out["custo_milheiro"], 7.0)
        self.assertAlmostEqual(out["effective_ratio"], 2.0)

    def test_transfer_with_club_bonus_additive(self):
        # 80% campanha + 40% clube Livelo = 120% → 2.2 dest per source
        out = m.transfer_milheiro(14, 1.0, bonus_pct=80, club_bonus_pct=40)
        self.assertAlmostEqual(out["effective_ratio"], 2.2)
        self.assertAlmostEqual(out["custo_milheiro"], round(14 / 2.2, 4))

    def test_club_subscription_uses_caller_fee_only(self):
        # Caller said R$ 50 / 1.000 miles. Tool must not inject a catalog price.
        out = m.club_milheiro(monthly_fee_brl=50, monthly_miles=1_000)
        self.assertAlmostEqual(out["custo_milheiro"], 50.0)
        self.assertEqual(out["monthly_fee_brl"], 50)
        self.assertIn("caller-supplied", out["disclaimer"].lower() + out["disclaimer"])

    def test_club_annual_extra_miles(self):
        # 12 × R$ 40 for 1_000/mês + 2_000 adesao = 14_000 miles, R$ 480
        out = m.club_milheiro(40, 1_000, extra_miles=2_000, months=12)
        self.assertAlmostEqual(out["miles_credited"], 14_000)
        self.assertAlmostEqual(out["total_paid_brl"], 480)
        self.assertAlmostEqual(out["custo_milheiro"], round(480 * 1000 / 14_000, 4))

    def test_redemption_subtracts_taxes(self):
        out = m.redemption_milheiro(cash_brl=2_000, miles=20_000, taxes_brl=200)
        self.assertAlmostEqual(out["saved_brl"], 1_800)
        self.assertAlmostEqual(out["valor_milheiro"], 90.0)

    def test_compare_points_win_when_valor_exceeds_custo(self):
        out = m.compare_acquisition_to_redemption(custo=15, valor=40)
        self.assertEqual(out["verdict"], "USE_POINTS")
        self.assertGreater(out["multiple"], 2)

    def test_compare_cash_wins_on_tie_and_loss(self):
        self.assertEqual(m.compare_acquisition_to_redemption(20, 20)["verdict"], "PAY_CASH")
        self.assertEqual(m.compare_acquisition_to_redemption(20, 10)["verdict"], "PAY_CASH")

    def test_label_bands(self):
        self.assertEqual(m.label_acquisition(10), "excepcional")
        self.assertEqual(m.label_acquisition(15), "bom")
        self.assertEqual(m.label_acquisition(22), "ok")
        self.assertEqual(m.label_acquisition(30), "fraco")
        self.assertEqual(m.label_acquisition(50), "ruim")


class ValidationTests(unittest.TestCase):
    def test_rejects_zero_miles(self):
        with self.assertRaises(m.MilheiroError):
            m.custo_milheiro(100, 0)

    def test_rejects_negative_price(self):
        with self.assertRaises(m.MilheiroError):
            m.custo_milheiro(-1, 1000)

    def test_rejects_negative_bonus(self):
        with self.assertRaises(m.MilheiroError):
            m.miles_credited(1000, bonus_pct=-10)

    def test_rejects_bad_bonus_mode(self):
        with self.assertRaises(m.MilheiroError):
            m.miles_credited(1000, bonus_mode="stacked")  # type: ignore[arg-type]

    def test_rejects_taxes_above_cash(self):
        with self.assertRaises(m.MilheiroError):
            m.redemption_milheiro(100, 1000, taxes_brl=150)

    def test_rejects_zero_ratio(self):
        with self.assertRaises(m.MilheiroError):
            m.transfer_milheiro(14, ratio=0)


class CliTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, _SCRIPT, *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_purchase_json(self):
        proc = self._run(
            "--json", "purchase", "--price", "270", "--miles", "10000", "--bonus-pct", "80"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["kind"], "purchase")
        self.assertAlmostEqual(data["miles_credited"], 18_000)
        self.assertAlmostEqual(data["custo_milheiro"], 15.0)

    def test_cli_requires_club_fee_no_default_price(self):
        proc = self._run("--json", "club", "--monthly-miles", "1000")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("monthly-fee", proc.stderr)

    def test_cli_compare(self):
        proc = self._run("--json", "compare", "--custo", "16", "--valor", "48")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["verdict"], "USE_POINTS")

    def test_cli_invalid_exits_1(self):
        proc = self._run("--json", "purchase", "--price", "10", "--miles", "0")
        self.assertEqual(proc.returncode, 1)


class NoLivePriceTests(unittest.TestCase):
    """Guardrails: the module must not ship hardcoded club/promo prices."""

    def test_source_has_no_default_club_fee(self):
        with open(_SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        for needle in ("54.90", "59.90", "69.90", "79.90", "89.90"):
            self.assertNotIn(needle, src, f"hardcoded-looking club fee {needle}")

    def test_parser_requires_price_and_club_fee(self):
        self.assertIn("All prices are inputs", m.build_parser().format_help())
        proc = subprocess.run(
            [sys.executable, _SCRIPT, "purchase", "--miles", "1000"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--price", proc.stderr)


if __name__ == "__main__":
    unittest.main()
