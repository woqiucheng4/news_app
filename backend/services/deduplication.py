"""
Deduplication service implementation.
"""

from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Any
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from datasketch import MinHash

from .interfaces import IDeduplicationService
from repositories.interfaces import IArticleRepository


class DeduplicationService(IDeduplicationService):
    """Three-layer deduplication service."""

    def __init__(
        self,
        article_repo: IArticleRepository,
        title_similarity_threshold: float = 0.7,
        simhash_distance_threshold: int = 3,
        candidate_limit: int = 200,
    ) -> None:
        self.article_repo = article_repo
        self.title_similarity_threshold = title_similarity_threshold
        self.simhash_distance_threshold = simhash_distance_threshold
        self.candidate_limit = candidate_limit

    async def check_duplicate(self, article_data: Dict) -> Dict:
        normalized_url = self._normalize_url(article_data.get("url", ""))
        url_hash = self._sha256(normalized_url) if normalized_url else ""

        # Layer 1: exact URL hash match.
        if url_hash:
            existing = await self.article_repo.get_by_url_hash(url_hash)
            if existing:
                return self._duplicate_result(
                    existing,
                    similarity=1.0,
                    layer="url_hash",
                )

        candidates = await self.article_repo.get_recent(limit=self.candidate_limit)
        incoming_title = article_data.get("title", "")
        incoming_content = article_data.get("content", "")

        # Layer 2: title similarity with MinHash + Jaccard.
        best_title_match = None
        best_title_score = 0.0
        for candidate in candidates:
            score = self._title_similarity(incoming_title, candidate.title or "")
            if score > best_title_score:
                best_title_score = score
                best_title_match = candidate

        if best_title_match and best_title_score >= self.title_similarity_threshold:
            return self._duplicate_result(
                best_title_match,
                similarity=best_title_score,
                layer="title_minhash",
            )

        # Layer 3: content fingerprint with SimHash + Hamming distance.
        incoming_simhash = self._simhash_hex(incoming_content or incoming_title)
        if incoming_simhash:
            best_content_match = None
            best_content_distance = None
            for candidate in candidates:
                candidate_simhash = candidate.simhash or self._simhash_hex(
                    candidate.content or candidate.title or ""
                )
                if not candidate_simhash:
                    continue
                distance = self._hamming_distance_hex(incoming_simhash, candidate_simhash)
                if best_content_distance is None or distance < best_content_distance:
                    best_content_distance = distance
                    best_content_match = candidate

            if (
                best_content_match is not None
                and best_content_distance is not None
                and best_content_distance <= self.simhash_distance_threshold
            ):
                similarity = 1 - (best_content_distance / 64)
                return self._duplicate_result(
                    best_content_match,
                    similarity=round(similarity, 4),
                    layer="content_simhash",
                )

        return {
            "is_duplicate": False,
            "duplicate_of": None,
            "event_id": None,
            "similarity": 0.0,
            "layer": None,
        }

    async def find_similar_articles(
        self,
        title: str,
        content: str,
        limit: int = 10,
    ) -> List[Dict]:
        candidates = await self.article_repo.get_recent(limit=max(limit * 10, 50))
        incoming_simhash = self._simhash_hex(content or title)
        results: List[Dict] = []

        for candidate in candidates:
            title_score = self._title_similarity(title, candidate.title or "")
            content_similarity = 0.0
            candidate_simhash = candidate.simhash or self._simhash_hex(
                candidate.content or candidate.title or ""
            )
            if incoming_simhash and candidate_simhash:
                distance = self._hamming_distance_hex(incoming_simhash, candidate_simhash)
                content_similarity = 1 - (distance / 64)

            score = max(title_score, content_similarity)
            if score <= 0:
                continue

            results.append(
                {
                    "id": str(candidate.id),
                    "event_id": str(candidate.event_id) if candidate.event_id else None,
                    "title": candidate.title,
                    "score": round(score, 4),
                    "title_similarity": round(title_score, 4),
                    "content_similarity": round(content_similarity, 4),
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]

    async def cluster_articles(self, articles: List[Dict]) -> List[List[str]]:
        clusters: List[List[int]] = []

        for i, article in enumerate(articles):
            placed = False
            for cluster in clusters:
                representative = articles[cluster[0]]
                title_score = self._title_similarity(
                    article.get("title", ""),
                    representative.get("title", ""),
                )
                content_distance = self._simhash_distance_from_text(
                    article.get("content", "") or article.get("title", ""),
                    representative.get("content", "") or representative.get("title", ""),
                )

                if (
                    title_score >= self.title_similarity_threshold
                    or content_distance <= self.simhash_distance_threshold
                ):
                    cluster.append(i)
                    placed = True
                    break

            if not placed:
                clusters.append([i])

        grouped_ids: List[List[str]] = []
        for cluster in clusters:
            grouped_ids.append(
                [str(articles[index]["id"]) for index in cluster if articles[index].get("id")]
            )
        return grouped_ids

    def _duplicate_result(self, article: Any, similarity: float, layer: str) -> Dict:
        return {
            "is_duplicate": True,
            "duplicate_of": str(article.id),
            "event_id": str(article.event_id) if article.event_id else None,
            "similarity": round(similarity, 4),
            "layer": layer,
        }

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        split = urlsplit(url.strip())
        filtered_query = [
            (k, v)
            for k, v in parse_qsl(split.query, keep_blank_values=True)
            if not (
                k.lower().startswith("utm_")
                or k.lower() in {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}
            )
        ]
        normalized_query = urlencode(sorted(filtered_query))
        normalized = urlunsplit(
            (
                split.scheme.lower(),
                split.netloc.lower(),
                split.path.rstrip("/") or "/",
                normalized_query,
                "",
            )
        )
        return normalized

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower())

    def _title_similarity(self, left: str, right: str) -> float:
        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens or not right_tokens:
            return 0.0

        left_minhash = MinHash(num_perm=128)
        right_minhash = MinHash(num_perm=128)
        for token in left_tokens:
            left_minhash.update(token.encode("utf-8"))
        for token in right_tokens:
            right_minhash.update(token.encode("utf-8"))
        return float(left_minhash.jaccard(right_minhash))

    def compute_simhash(self, text: str) -> str:
        return self._simhash_hex(text)

    def _simhash_hex(self, text: str) -> str:
        tokens = self._tokenize(text)
        if not tokens:
            return ""

        bits = [0] * 64
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            for i in range(64):
                mask = 1 << i
                bits[i] += 1 if token_hash & mask else -1

        fingerprint = 0
        for i, value in enumerate(bits):
            if value > 0:
                fingerprint |= 1 << i
        return f"{fingerprint:016x}"

    @staticmethod
    def _hamming_distance_hex(left_hex: str, right_hex: str) -> int:
        left = int(left_hex, 16)
        right = int(right_hex, 16)
        xor_value = left ^ right
        # Python 3.9 compatibility: int.bit_count() is only available in 3.10+.
        return bin(xor_value).count("1")

    def _simhash_distance_from_text(self, left_text: str, right_text: str) -> int:
        left = self._simhash_hex(left_text)
        right = self._simhash_hex(right_text)
        if not left or not right:
            return 64
        return self._hamming_distance_hex(left, right)
