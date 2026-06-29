import re
import unicodedata
from abc import ABC, abstractmethod

from rapidfuzz import fuzz

from app.models.product_interest import ProductInterest


PRICE_PATTERNS = [
    re.compile(r"R?\$\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"(\d+[\.,]\d+)\s*reais", re.IGNORECASE),
    re.compile(r"(\d+[\.,]\d+)\s*rea[l]s?", re.IGNORECASE),
    re.compile(r"(\d+)\s*reais", re.IGNORECASE),
    re.compile(r"(\d+)\s*rea[l]s?", re.IGNORECASE),
    re.compile(r"preço\s*:?\s*R?\$\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"por\s*R?\$\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"apenas\s*R?\$\s*([\d.,]+)", re.IGNORECASE),
]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_price(raw: str) -> float | None:
    """Converte um valor monetário cru (BR/US) em float.

    - '.' e ',' presentes -> '.' = milhar, ',' = decimal (padrão BR): '1.234,56' -> 1234.56
    - só ',' -> decimal: '9,99' -> 9.99
    - só '.' com exatamente 2 casas finais -> decimal: '9.99' -> 9.99
    - só '.' caso contrário -> milhar: '10.000' -> 10000
    """
    raw = raw.strip()
    if not raw:
        return None

    has_dot = "." in raw
    has_comma = "," in raw

    if has_dot and has_comma:
        normalized = raw.replace(".", "").replace(",", ".")
    elif has_comma:
        normalized = raw.replace(",", ".")
    elif has_dot:
        if re.fullmatch(r"\d+\.\d{2}", raw):
            normalized = raw
        else:
            normalized = raw.replace(".", "")
    else:
        normalized = raw

    try:
        price = float(normalized)
    except ValueError:
        return None
    return price if price > 0 else None


def extract_prices(text: str) -> list[float]:
    prices: list[float] = []
    for pattern in PRICE_PATTERNS:
        for match in pattern.finditer(text):
            price = _parse_price(match.group(1))
            if price is not None:
                prices.append(price)
    return prices


class MatchStrategy(ABC):
    @abstractmethod
    def compute_score(self, normalized: str, interest: ProductInterest) -> float: ...


class KeywordMatchStrategy(MatchStrategy):
    """Semântica OU: qualquer palavra-chave presente (fronteira de palavra) qualifica."""

    def matched_keyword(self, normalized: str, interest: ProductInterest) -> str | None:
        """Retorna a primeira palavra-chave (forma original) presente no texto."""
        for kw in interest.palavras_chave or []:
            norm_kw = normalize_text(kw)
            if not norm_kw:
                continue
            if re.search(rf"\b{re.escape(norm_kw)}\b", normalized):
                return kw
        return None

    def compute_score(self, normalized: str, interest: ProductInterest) -> float:
        return 1.0 if self.matched_keyword(normalized, interest) else 0.0


class FuzzyMatchStrategy(MatchStrategy):
    def compute_score(self, normalized: str, interest: ProductInterest) -> float:
        produto = normalize_text(interest.nome_produto)
        if not produto:
            return 0.0
        return fuzz.token_set_ratio(produto, normalized) / 100.0


class CompositeMatcher:
    def __init__(self) -> None:
        self.strategies: dict[str, MatchStrategy] = {
            "keyword": KeywordMatchStrategy(),
            "fuzzy": FuzzyMatchStrategy(),
        }

    def _is_excluded(self, normalized: str, interest: ProductInterest) -> bool:
        for excl in interest.palavras_excluidas:
            norm_excl = normalize_text(excl)
            if norm_excl and norm_excl in normalized:
                return True
        return False

    def _has_keywords(self, interest: ProductInterest) -> bool:
        """Há ao menos uma palavra-chave não vazia após normalização?"""
        return any(normalize_text(kw) for kw in interest.palavras_chave or [])

    def score_breakdown(
        self, text: str, interest: ProductInterest
    ) -> tuple[float, dict[str, float]]:
        if not text:
            return 0.0, {name: 0.0 for name in self.strategies}
        normalized = normalize_text(text)
        if self._is_excluded(normalized, interest):
            return 0.0, {name: 0.0 for name in self.strategies}
        # Palavra-chave manda: se o interesse define palavras-chave, a mensagem
        # precisa conter uma delas. A similaridade fuzzy com o nome do produto só
        # vale como fallback quando NÃO há palavras-chave definidas.
        keyword_score = self.strategies["keyword"].compute_score(normalized, interest)
        if self._has_keywords(interest):
            fuzzy_score = 0.0
        else:
            fuzzy_score = self.strategies["fuzzy"].compute_score(normalized, interest)
        breakdown = {"keyword": keyword_score, "fuzzy": fuzzy_score}
        return max(breakdown.values(), default=0.0), breakdown

    def compute_score(self, text: str, interest: ProductInterest) -> float:
        score, _ = self.score_breakdown(text, interest)
        return score

    def matched_term(self, text: str, interest: ProductInterest) -> str | None:
        """Explica o match: a palavra-chave que disparou ou, no caso de só a
        similaridade fuzzy ter qualificado, o próprio nome do produto."""
        if not text:
            return None
        normalized = normalize_text(text)
        if self._is_excluded(normalized, interest):
            return None
        kw = self.strategies["keyword"].matched_keyword(normalized, interest)  # type: ignore[attr-defined]
        if kw is not None:
            return kw
        # Fallback pelo nome do produto só quando o match veio da similaridade
        # fuzzy — isto é, quando o interesse não tem palavras-chave definidas.
        if self._has_keywords(interest):
            return None
        if self.strategies["fuzzy"].compute_score(normalized, interest) > 0:
            return interest.nome_produto
        return None

    def match(
        self, text: str, interest: ProductInterest
    ) -> tuple[float, list[float], dict[str, float], str | None]:
        score, breakdown = self.score_breakdown(text, interest)
        prices = extract_prices(text)
        matched = self.matched_term(text, interest) if score > 0 else None
        return score, prices, breakdown, matched


composite_matcher = CompositeMatcher()
