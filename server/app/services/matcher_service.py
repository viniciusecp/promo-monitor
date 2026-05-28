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


def extract_prices(text: str) -> list[float]:
    prices: list[float] = []
    for pattern in PRICE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1).replace(".", "").replace(",", ".")
            try:
                price = float(raw)
                if price > 0:
                    prices.append(price)
            except ValueError:
                continue
    return prices


class MatchStrategy(ABC):
    @abstractmethod
    def compute_score(self, text: str, interest: ProductInterest) -> float: ...


class KeywordMatchStrategy(MatchStrategy):
    def compute_score(self, text: str, interest: ProductInterest) -> float:
        normalized = normalize_text(text)
        hits = 0
        for kw in interest.palavras_chave:
            if normalize_text(kw) in normalized:
                hits += 1
        if not interest.palavras_chave:
            return 0.0
        return min(hits / len(interest.palavras_chave), 1.0)


class FuzzyMatchStrategy(MatchStrategy):
    def compute_score(self, text: str, interest: ProductInterest) -> float:
        normalized = normalize_text(text)
        produto = normalize_text(interest.nome_produto)
        if not produto:
            return 0.0
        ratio = fuzz.partial_ratio(produto, normalized) / 100.0
        return ratio


class CompositeMatcher:
    def __init__(self) -> None:
        self.strategies: list[MatchStrategy] = [
            KeywordMatchStrategy(),
            FuzzyMatchStrategy(),
        ]

    def compute_score(self, text: str, interest: ProductInterest) -> float:
        if not text:
            return 0.0
        normalized = normalize_text(text)
        for excl in interest.palavras_excluidas:
            if normalize_text(excl) in normalized:
                return 0.0
        scores = [s.compute_score(text, interest) for s in self.strategies]
        return max(scores)

    def match(self, text: str, interest: ProductInterest) -> tuple[float, list[float]]:
        score = self.compute_score(text, interest)
        prices = extract_prices(text)
        return score, prices


composite_matcher = CompositeMatcher()
