"""
Knowledge Base Engine — Structured knowledge storage and querying.

Provides:
- KnowledgeEntry dataclass for individual knowledge items
- KnowledgeBase for storing, indexing, and querying knowledge
- Category-based organization and full-text search
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeEntry:
    """A single knowledge item."""
    key: str
    title: str
    content: str
    category: str
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    references: tuple[str, ...] = ()  # References to other entries

    def payload(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "references": list(self.references),
        }

    def matches_query(self, query: str) -> bool:
        """Check if this entry matches a text query."""
        query_lower = query.lower()
        return (
            query_lower in self.key.lower()
            or query_lower in self.title.lower()
            or query_lower in self.content.lower()
            or any(query_lower in t.lower() for t in self.tags)
        )


@dataclass
class KnowledgeQuery:
    """A query against the knowledge base."""
    text: str = ""
    category: str | None = None
    tags: tuple[str, ...] = ()
    max_results: int = 50
    sort_by: str = "relevance"  # "relevance", "key", "title"

    def matches(self, entry: KnowledgeEntry) -> bool:
        if self.category and entry.category != self.category:
            return False
        if self.tags and not any(t in entry.tags for t in self.tags):
            return False
        if self.text and not entry.matches_query(self.text):
            return False
        return True


class KnowledgeBase:
    """
    Structured knowledge storage with indexing and querying.

    Supports:
    - Add/remove entries
    - Category-based listing
    - Tag-based filtering
    - Full-text search
    - JSON import/export
    - Cross-references between entries
    """

    def __init__(self):
        self._entries: dict[str, KnowledgeEntry] = {}
        self._category_index: dict[str, set[str]] = {}  # category -> set of keys
        self._tag_index: dict[str, set[str]] = {}  # tag -> set of keys

    # ------------------------------------------------------------------
    # Entry management
    # ------------------------------------------------------------------
    def add(self, entry: KnowledgeEntry) -> None:
        """Add a knowledge entry."""
        if entry.key in self._entries:
            raise ValueError(f"Knowledge entry already exists: {entry.key}")
        self._entries[entry.key] = entry

        # Update indexes
        self._category_index.setdefault(entry.category, set()).add(entry.key)
        for tag in entry.tags:
            self._tag_index.setdefault(tag, set()).add(entry.key)

    def remove(self, key: str) -> KnowledgeEntry | None:
        """Remove and return a knowledge entry."""
        entry = self._entries.pop(key, None)
        if entry is None:
            return None
        # Clean indexes
        cat_keys = self._category_index.get(entry.category)
        if cat_keys:
            cat_keys.discard(key)
            if not cat_keys:
                self._category_index.pop(entry.category, None)
        for tag in entry.tags:
            tag_keys = self._tag_index.get(tag)
            if tag_keys:
                tag_keys.discard(key)
                if not tag_keys:
                    self._tag_index.pop(tag, None)
        return entry

    def get(self, key: str) -> KnowledgeEntry | None:
        """Get a single entry by key."""
        return self._entries.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------
    def query(self, query: KnowledgeQuery | str) -> list[KnowledgeEntry]:
        """
        Query the knowledge base.

        Parameters
        ----------
        query : KnowledgeQuery | str
            Either a structured query object or a plain text search string.

        Returns
        -------
        list[KnowledgeEntry]
            Matching entries sorted by relevance.
        """
        if isinstance(query, str):
            q = KnowledgeQuery(text=query)
        else:
            q = query

        results = [e for e in self._entries.values() if q.matches(e)]

        # Sort
        if q.sort_by == "key":
            results.sort(key=lambda e: e.key)
        elif q.sort_by == "title":
            results.sort(key=lambda e: e.title)
        else:  # relevance
            results.sort(key=lambda e: self._relevance_score(e, q.text), reverse=True)

        return results[: q.max_results]

    def search(self, text: str, *, category: str | None = None) -> list[KnowledgeEntry]:
        """Convenience method for simple text search."""
        q = KnowledgeQuery(text=text, category=category)
        return self.query(q)

    def list_by_category(self, category: str) -> list[KnowledgeEntry]:
        """List all entries in a category."""
        keys = self._category_index.get(category, set())
        entries = [self._entries[k] for k in keys if k in self._entries]
        entries.sort(key=lambda e: e.title)
        return entries

    def list_by_tag(self, tag: str) -> list[KnowledgeEntry]:
        """List all entries with a given tag."""
        keys = self._tag_index.get(tag, set())
        entries = [self._entries[k] for k in keys if k in self._entries]
        entries.sort(key=lambda e: e.title)
        return entries

    def list_categories(self) -> list[str]:
        return sorted(self._category_index.keys())

    def list_tags(self) -> list[str]:
        return sorted(self._tag_index.keys())

    def get_entry_count(self) -> int:
        return len(self._entries)

    def get_category_counts(self) -> dict[str, int]:
        return {cat: len(keys) for cat, keys in self._category_index.items()}

    # ------------------------------------------------------------------
    # Import/Export
    # ------------------------------------------------------------------
    def load_from_json(self, path: str | Path) -> int:
        """
        Load entries from a JSON file.

        Expected format:
        {
            "knowledge": [
                {
                    "key": "...",
                    "title": "...",
                    "content": "...",
                    "category": "...",
                    "tags": [],
                    "metadata": {},
                    "references": []
                }
            ]
        }

        Returns the number of entries loaded.
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        count = 0
        for item in data.get("knowledge", []):
            try:
                entry = KnowledgeEntry(
                    key=item["key"],
                    title=item.get("title", item["key"]),
                    content=item.get("content", ""),
                    category=item.get("category", "general"),
                    tags=tuple(item.get("tags", [])),
                    metadata=item.get("metadata", {}),
                    references=tuple(item.get("references", [])),
                )
                self.add(entry)
                count += 1
            except (ValueError, KeyError) as exc:
                pass  # Skip malformed entries silently
        return count

    def save_to_json(self, path: str | Path) -> None:
        """Save all entries to a JSON file."""
        data = {
            "knowledge": [e.payload() for e in self._entries.values()]
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        """Convert entire knowledge base to a dict."""
        return {
            "entries": {k: e.payload() for k, e in self._entries.items()},
            "categories": self.list_categories(),
            "tags": self.list_tags(),
            "counts": self.get_category_counts(),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    @staticmethod
    def _relevance_score(entry: KnowledgeEntry, query_text: str) -> float:
        """Calculate relevance score for a query."""
        if not query_text:
            return 1.0
        query_lower = query_text.lower()
        score = 0.0

        # Title match is highest weight
        if query_lower in entry.title.lower():
            score += 10.0

        # Key match
        if query_lower in entry.key.lower():
            score += 8.0

        # Content match (partial, based on frequency)
        count = entry.content.lower().count(query_lower)
        score += min(count * 0.5, 5.0)

        # Tag match
        if any(query_lower in t.lower() for t in entry.tags):
            score += 3.0

        return score
