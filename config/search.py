"""Full-text search in PostgreSQL with Russian morphology: "Сибирь" also finds "Сибири"."""

from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank, SearchVector
from django.db.models import Q, QuerySet, Value
from django.db.models.functions import Coalesce, NullIf

CONFIG = "russian"
LIMIT = 50
MAX_QUERY_LENGTH = 200


def full_text_search(
    queryset: QuerySet,
    query: str,
    weights: dict[str, str],
    headline_fields: tuple[str, ...],
) -> QuerySet:
    """
    Matches of `query` in `queryset`, best first, at most LIMIT.

    weights: field -> weight "A".."D" (a match in the title outranks one in the text).
    headline_fields: where to take the snippet from — the first non-empty of them.
    Each result gets `headline`: a fragment with matches wrapped in <mark></mark>.
    The query uses web-search syntax: "exact phrase", -exclude, or.
    """
    query = query.strip()[:MAX_QUERY_LENGTH]
    if not query:
        return queryset.none()

    vector = None
    for field, weight in weights.items():
        part = SearchVector(field, weight=weight, config=CONFIG)
        vector = part if vector is None else vector + part
    search_query = SearchQuery(query, config=CONFIG, search_type="websearch")

    sources = [NullIf(f, Value("")) for f in headline_fields]
    source = Coalesce(*sources) if len(sources) > 1 else headline_fields[0]
    return (
        queryset.annotate(search=vector, rank=SearchRank(vector, search_query))
        # part of a word in the title is found too: "Сиб" → "Сибирь"
        .filter(Q(search=search_query) | Q(title__icontains=query))
        .annotate(
            headline=SearchHeadline(
                source,
                search_query,
                config=CONFIG,
                start_sel="<mark>",
                stop_sel="</mark>",
                min_words=15,
                max_words=35,
                max_fragments=1,
            )
        )
        .order_by("-rank", "pk")[:LIMIT]
    )
