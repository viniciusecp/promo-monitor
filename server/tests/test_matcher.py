"""Testes do matcher. Rodar a partir de server/:

    python -m pytest tests/test_matcher.py        # se pytest instalado
    python tests/test_matcher.py                  # fallback sem pytest
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.product_interest import ProductInterest
from app.services.matcher_service import (
    composite_matcher,
    extract_prices,
    normalize_text,
)


def _interest(
    nome_produto: str = "produto",
    palavras_chave: list[str] | None = None,
    palavras_excluidas: list[str] | None = None,
    preco_maximo: float | None = None,
) -> ProductInterest:
    return ProductInterest(
        nome_produto=nome_produto,
        palavras_chave=palavras_chave or [],
        palavras_excluidas=palavras_excluidas or [],
        preco_maximo=preco_maximo,
        ativo=True,
    )


def test_keyword_word_boundary_no_false_substring():
    interest = _interest(nome_produto="zzzzz", palavras_chave=["tv"])
    score, _ = composite_matcher.score_breakdown("creme nativa hidratante", interest)
    assert score < 0.6, f"esperava sem match, veio {score}"


def test_keyword_word_boundary_match():
    interest = _interest(nome_produto="zzzzz", palavras_chave=["tv"])
    score, breakdown = composite_matcher.score_breakdown(
        "promo smart tv 50 polegadas", interest
    )
    assert breakdown["keyword"] == 1.0
    assert score == 1.0


def test_keyword_or_semantics_any_one_matches():
    interest = _interest(
        nome_produto="zzzzz", palavras_chave=["geladeira", "fogao", "microondas"]
    )
    score, breakdown = composite_matcher.score_breakdown(
        "oferta de microondas 30L", interest
    )
    assert breakdown["keyword"] == 1.0
    assert score == 1.0


def test_fuzzy_handles_token_reorder():
    interest = _interest(nome_produto="monitor LG 27")
    score, breakdown = composite_matcher.score_breakdown(
        "LG 27 polegadas monitor gamer full hd", interest
    )
    assert breakdown["fuzzy"] >= 0.6, breakdown
    assert score >= 0.6


def test_keyword_authoritative_blocks_name_only_match():
    """Com palavras-chave definidas, a similaridade com o nome do produto não
    pode mais qualificar sozinha."""
    interest = _interest(nome_produto="Monitor", palavras_chave=['monitor 34"'])
    score, breakdown = composite_matcher.score_breakdown(
        "Monitor gamer 27 polegadas", interest
    )
    assert breakdown["fuzzy"] == 0.0, breakdown
    assert score < 0.6, f"esperava sem match, veio {score}"


def test_keyword_authoritative_matches_literal_keyword():
    interest = _interest(nome_produto="Monitor", palavras_chave=['monitor 34"'])
    score, prices, breakdown, matched = composite_matcher.match(
        "Monitor 34 polegadas ultrawide", interest
    )
    assert breakdown["keyword"] == 1.0
    assert score == 1.0
    assert matched == 'monitor 34"', matched


def test_excluded_word_vetoes():
    interest = _interest(
        nome_produto="notebook dell", palavras_chave=["notebook"],
        palavras_excluidas=["usado"],
    )
    score, _ = composite_matcher.score_breakdown(
        "notebook dell usado em bom estado", interest
    )
    assert score == 0.0


def test_price_lowest_de_para():
    prices = extract_prices("de R$ 1.234,56 por R$ 999,90")
    assert min(prices) == 999.90, prices


def test_price_us_decimal_dot():
    prices = extract_prices("apenas R$ 9.99")
    assert 9.99 in prices, prices


def test_price_thousands_dot():
    prices = extract_prices("R$ 10.000")
    assert 10000.0 in prices, prices


def test_normalize_strips_accents():
    assert normalize_text("Promoção Relâmpago!") == "promocao relampago"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
