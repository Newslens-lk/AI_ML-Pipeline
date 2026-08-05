"""Pydantic Article model — single source of truth for the corpus schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


def make_article_id(source_dataset: str, url: str) -> str:
    """Deterministic UUID5 from (source_dataset, url)."""
    namespace = uuid.UUID("a3f0b1c2-d4e5-6789-abcd-ef0123456789")
    return str(uuid.uuid5(namespace, f"{source_dataset}:{url}"))


class Article(BaseModel):
    # Layer 1 — required
    article_id: str
    source_dataset: str
    publisher: str
    url: str
    published_at: datetime
    title: str
    body_text: str
    language: str
    content_hash: str

    # Layer 2 — optional
    category: Optional[str] = None
    author: Optional[str] = None
    raw_path: Optional[str] = None

    # Layer 3 — reserved, null in Phase 1
    event_cluster_id: Optional[str] = None
    embedding_ref: Optional[str] = None
    bias_label: Optional[str] = None
    bias_confidence: Optional[float] = None
    annotator_id: Optional[str] = None
    annotation_timestamp: Optional[datetime] = None
