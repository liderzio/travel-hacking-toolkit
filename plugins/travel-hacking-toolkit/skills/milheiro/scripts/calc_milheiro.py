#!/usr/bin/env python3
"""Custo do milheiro in BRL — acquisition, club, transfer, and redemption.

Every money figure is an INPUT. This tool never looks up live club prices,
never logs into an account, and never treats a blog number as a default.

    custo_do_milheiro = total_pago_BRL * 1000 / milhas_creditadas

Brazilian promo banners usually ADD bonus percentages
(80% campaign + 30% club = 110%). That is ``additive``. Use
``multiplicative`` only when the regulation says bonuses apply in sequence.

Examples (illustrative numbers, not live offers)::

    python3 skills/milheiro/scripts/calc_milheiro.py purchase \\
        --price 270 --miles 10000 --bonus-pct 80 --club-bonus-pct 30

    python3 skills/milheiro/scripts/calc_milheiro.py club \\
        --monthly-fee 50 --monthly-miles 1000

    python3 skills/milheiro/scripts/calc_milheiro.py transfer \\
        --source-milheiro 14 --ratio 1 --bonus-pct 100

    python3 skills/milheiro/scripts/calc_milheiro.py redeem \\
        --cash 1800 --taxes 120 --miles 20000
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Literal

BonusMode = Literal["additive", "multiplicative"]

# Community heuristics for labelling an acquisition milheiro.
# Overridable; never treated as a published valuation.
DEFAULT_BANDS = (
    (12.0, "excepcional"),
    (18.0, "bom"),
    (25.0, "ok"),
    (35.0, "fraco"),
    (None, "ruim"),
)


class MilheiroError(ValueError):
    """Invalid input for a milheiro calculation."""


def miles_credited(
    base_miles: float,
    bonus_pct: float = 0.0,
    club_bonus_pct: float = 0.0,
    bonus_mode: BonusMode = "additive",
) -> float:
    """Miles/points actually credited after campaign + club bonuses."""
    if base_miles < 0:
        raise MilheiroError("base_miles must be >= 0")
    if bonus_pct < 0 or club_bonus_pct < 0:
        raise MilheiroError("bonus percentages must be >= 0")
    if bonus_mode == "additive":
        return base_miles * (1.0 + (bonus_pct + club_bonus_pct) / 100.0)
    if bonus_mode == "multiplicative":
        return base_miles * (1.0 + bonus_pct / 100.0) * (1.0 + club_bonus_pct / 100.0)
    raise MilheiroError(f"unknown bonus_mode: {bonus_mode}")


def custo_milheiro(price_brl: float, miles: float) -> float:
    """BRL paid per 1,000 miles/points."""
    if miles <= 0:
        raise MilheiroError("miles must be > 0")
    if price_brl < 0:
        raise MilheiroError("price_brl must be >= 0")
    return price_brl * 1000.0 / miles


def label_acquisition(custo: float, bands: tuple = DEFAULT_BANDS) -> str:
    """Heuristic label for an acquisition milheiro. Not a fact about value."""
    for max_inclusive, name in bands:
        if max_inclusive is None or custo <= max_inclusive:
            return name
    return "ruim"


def purchase_milheiro(
    price_brl: float,
    base_miles: float,
    bonus_pct: float = 0.0,
    club_bonus_pct: float = 0.0,
    bonus_mode: BonusMode = "additive",
    extra_fee_brl: float = 0.0,
) -> dict[str, Any]:
    """Miles purchase (compra de milhas) or a priced bundle of points."""
    if extra_fee_brl < 0:
        raise MilheiroError("extra_fee_brl must be >= 0")
    credited = miles_credited(base_miles, bonus_pct, club_bonus_pct, bonus_mode)
    total_paid = price_brl + extra_fee_brl
    custo = custo_milheiro(total_paid, credited)
    return {
        "kind": "purchase",
        "base_miles": base_miles,
        "bonus_pct": bonus_pct,
        "club_bonus_pct": club_bonus_pct,
        "bonus_mode": bonus_mode,
        "miles_credited": credited,
        "price_brl": price_brl,
        "extra_fee_brl": extra_fee_brl,
        "total_paid_brl": total_paid,
        "custo_milheiro": round(custo, 4),
        "label": label_acquisition(custo),
        "disclaimer": "Inputs are caller-supplied. Not a live offer.",
    }


def club_milheiro(
    monthly_fee_brl: float,
    monthly_miles: float,
    extra_miles: float = 0.0,
    months: int = 1,
) -> dict[str, Any]:
    """Club subscription milheiro from the fee and miles the caller provides.

    Does not look up Clube Smiles / Livelo / LATAM / Azul prices.
    """
    if months <= 0:
        raise MilheiroError("months must be >= 1")
    if extra_miles < 0:
        raise MilheiroError("extra_miles must be >= 0")
    total_miles = monthly_miles * months + extra_miles
    total_paid = monthly_fee_brl * months
    custo = custo_milheiro(total_paid, total_miles)
    return {
        "kind": "club",
        "monthly_fee_brl": monthly_fee_brl,
        "monthly_miles": monthly_miles,
        "extra_miles": extra_miles,
        "months": months,
        "miles_credited": total_miles,
        "total_paid_brl": total_paid,
        "custo_milheiro": round(custo, 4),
        "label": label_acquisition(custo),
        "disclaimer": "Club fee is caller-supplied. Never use a cached club price.",
    }


def transfer_milheiro(
    source_milheiro: float,
    ratio: float = 1.0,
    bonus_pct: float = 0.0,
    club_bonus_pct: float = 0.0,
    bonus_mode: BonusMode = "additive",
) -> dict[str, Any]:
    """Effective airline milheiro after transferring from a bank/coalition currency.

    ``ratio`` is dest_miles per 1 source point (1.0 = 1:1).
    Bonuses apply to the miles received, same stacking rules as purchases.
    """
    if source_milheiro < 0:
        raise MilheiroError("source_milheiro must be >= 0")
    if ratio <= 0:
        raise MilheiroError("ratio must be > 0")
    # 1000 source points cost `source_milheiro` BRL and become
    # 1000 * ratio * (1+bonuses) dest miles.
    dest_per_thousand_source = miles_credited(
        1000.0 * ratio, bonus_pct, club_bonus_pct, bonus_mode
    )
    custo = custo_milheiro(source_milheiro, dest_per_thousand_source)
    effective_ratio = dest_per_thousand_source / 1000.0
    return {
        "kind": "transfer",
        "source_milheiro": source_milheiro,
        "ratio": ratio,
        "bonus_pct": bonus_pct,
        "club_bonus_pct": club_bonus_pct,
        "bonus_mode": bonus_mode,
        "effective_ratio": round(effective_ratio, 6),
        "custo_milheiro": round(custo, 4),
        "label": label_acquisition(custo),
        "disclaimer": "Confirm the live transfer bonus on the coalition site before moving points. This tool does not transfer.",
    }


def redemption_milheiro(
    cash_brl: float,
    miles: float,
    taxes_brl: float = 0.0,
) -> dict[str, Any]:
    """Valor do milheiro: cash avoided per 1,000 award miles.

    Always subtract award taxes/fees still paid in cash.
    """
    if taxes_brl < 0:
        raise MilheiroError("taxes_brl must be >= 0")
    saved = cash_brl - taxes_brl
    if saved < 0:
        raise MilheiroError("taxes_brl cannot exceed cash_brl")
    valor = custo_milheiro(saved, miles)
    return {
        "kind": "redemption",
        "cash_brl": cash_brl,
        "taxes_brl": taxes_brl,
        "saved_brl": saved,
        "miles": miles,
        "valor_milheiro": round(valor, 4),
        "disclaimer": "Compare valor_milheiro with the acquisition custo_milheiro. If valor <= custo, pay cash.",
    }


def compare_acquisition_to_redemption(
    custo: float,
    valor: float,
) -> dict[str, Any]:
    """Should this award beat paying cash, given acquisition cost vs redemption value?"""
    if custo <= 0:
        raise MilheiroError("custo must be > 0")
    multiple = valor / custo
    if valor > custo:
        verdict = "USE_POINTS"
        reason = (
            f"Valor do milheiro (R$ {valor:.2f}) supera o custo (R$ {custo:.2f}). "
            f"{multiple:.2f}x. Pontos vencem cash neste trecho."
        )
    elif valor == custo:
        verdict = "PAY_CASH"
        reason = "Empate. Preserve pontos (opcionalidade)."
    else:
        verdict = "PAY_CASH"
        reason = (
            f"Valor do milheiro (R$ {valor:.2f}) e menor que o custo (R$ {custo:.2f}). "
            "Pague cash ou busque outro resgate."
        )
    return {
        "custo_milheiro": round(custo, 4),
        "valor_milheiro": round(valor, 4),
        "multiple": round(multiple, 4),
        "verdict": verdict,
        "reason": reason,
    }


def _print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    kind = result.get("kind", "")
    if kind == "redemption":
        print(f"valor do milheiro: R$ {result['valor_milheiro']:.2f}")
        print(f"economia:          R$ {result['saved_brl']:.2f}")
        print(f"milhas:            {result['miles']:.0f}")
    elif kind == "transfer":
        print(f"custo do milheiro: R$ {result['custo_milheiro']:.2f}  ({result['label']})")
        print(f"ratio efetivo:     {result['effective_ratio']:.4f} dest / 1 origem")
    else:
        print(f"custo do milheiro: R$ {result['custo_milheiro']:.2f}  ({result['label']})")
        print(f"milhas creditadas: {result['miles_credited']:.2f}")
        print(f"total pago:        R$ {result['total_paid_brl']:.2f}")
    print(result["disclaimer"])


def _add_bonus_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--bonus-pct", type=float, default=0.0, help="Campaign bonus percent (e.g. 80 for +80%%)")
    p.add_argument("--club-bonus-pct", type=float, default=0.0, help="Extra club bonus percent (e.g. 30)")
    p.add_argument(
        "--bonus-mode",
        choices=("additive", "multiplicative"),
        default="additive",
        help="additive (default, BR banners) or multiplicative",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Custo do milheiro (BRL / 1.000 milhas). All prices are inputs; nothing is fetched."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("purchase", help="Compra de milhas / pacote promocional")
    p.add_argument("--price", type=float, required=True, help="Price paid in BRL (caller-supplied)")
    p.add_argument("--miles", type=float, required=True, help="Base miles before bonus")
    p.add_argument("--extra-fee", type=float, default=0.0, help="Extra cash fee in BRL")
    _add_bonus_args(p)

    c = sub.add_parser("club", help="Assinatura de clube (fee informado pelo usuario)")
    c.add_argument("--monthly-fee", type=float, required=True, help="Monthly club fee in BRL (do NOT guess)")
    c.add_argument("--monthly-miles", type=float, required=True, help="Miles/points credited per month")
    c.add_argument("--extra-miles", type=float, default=0.0, help="One-shot extra miles (adesao)")
    c.add_argument("--months", type=int, default=1, help="Months to amortize")

    t = sub.add_parser("transfer", help="Transferencia coalizao/banco -> cia")
    t.add_argument("--source-milheiro", type=float, required=True, help="What 1.000 source points cost you, BRL")
    t.add_argument("--ratio", type=float, default=1.0, help="Dest miles per 1 source point (1.0 = 1:1)")
    _add_bonus_args(t)

    r = sub.add_parser("redeem", help="Valor do milheiro de um premio vs cash")
    r.add_argument("--cash", type=float, required=True, help="Cash fare in BRL")
    r.add_argument("--miles", type=float, required=True, help="Award miles required")
    r.add_argument("--taxes", type=float, default=0.0, help="Award taxes/fees still paid in BRL")

    x = sub.add_parser("compare", help="Custo de aquisicao vs valor de resgate")
    x.add_argument("--custo", type=float, required=True, help="Acquisition milheiro (BRL / 1.000)")
    x.add_argument("--valor", type=float, required=True, help="Redemption milheiro (BRL / 1.000)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.cmd == "purchase":
            result = purchase_milheiro(
                price_brl=args.price,
                base_miles=args.miles,
                bonus_pct=args.bonus_pct,
                club_bonus_pct=args.club_bonus_pct,
                bonus_mode=args.bonus_mode,
                extra_fee_brl=args.extra_fee,
            )
        elif args.cmd == "club":
            result = club_milheiro(
                monthly_fee_brl=args.monthly_fee,
                monthly_miles=args.monthly_miles,
                extra_miles=args.extra_miles,
                months=args.months,
            )
        elif args.cmd == "transfer":
            result = transfer_milheiro(
                source_milheiro=args.source_milheiro,
                ratio=args.ratio,
                bonus_pct=args.bonus_pct,
                club_bonus_pct=args.club_bonus_pct,
                bonus_mode=args.bonus_mode,
            )
        elif args.cmd == "redeem":
            result = redemption_milheiro(
                cash_brl=args.cash,
                miles=args.miles,
                taxes_brl=args.taxes,
            )
        elif args.cmd == "compare":
            result = compare_acquisition_to_redemption(args.custo, args.valor)
        else:
            parser.error(f"unknown command {args.cmd}")
            return 2
    except MilheiroError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_result(result, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
