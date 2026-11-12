"""Day 4, task 7: ask models for three academic citations on a niche topic, then verify each one.

A citation counts as REAL only if a paper with (almost) the same title exists in Crossref or OpenAlex
(two public scholarly databases), and the year and first author also match.

    uv run python tasks/task7_citations.py
    uv run python tasks/task7_citations.py --topic "your own niche topic" --models local gemini
"""

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx

from llm_client import (
    PROFILES,
    MissingConfigError,
    chat_messages,
    make_openai_client,
    model_name,
)

DEFAULT_TOPIC = (
    "tokenization efficiency of Gujarati text in multilingual large language models"
)
DEFAULT_MODELS = ["local", "gemini", "gemini:gemini-3.6-flash"]
RESULTS_FILE = Path(__file__).parent.parent / "results" / "task7_citations.json"
HEADERS = {"User-Agent": "ai-eng-learning/0.1 (learning project)"}
TITLE_MATCH = 0.85  # how similar two titles must be (0 to 1) to count as the same paper

FORMAT = (
    "Reply with only a JSON list of exactly three objects with the keys "
    '"authors" (list of full names), "year" (number), "title", "venue" and "doi" (empty string if unknown). '
    "No other text."
)
PROMPTS = {
    "plain": f"Give me three academic citations on this topic: {{topic}}. {FORMAT}",
    "careful": (
        "Give me up to three academic citations on this topic: {topic}. Only include a paper if you are certain "
        "it really exists with exactly this title, authors and year. If you are not certain, return fewer papers, "
        f"or an empty list. {FORMAT}"
    ),
}


@dataclass
class Citation:
    authors: list[str]
    year: int | None
    title: str
    venue: str
    doi: str


@dataclass
class Found:
    """A real paper found in a database."""

    source: str
    title: str
    year: int | None
    authors: list[str]
    doi: str


@dataclass
class Verdict:
    citation: Citation
    verdict: str  # REAL, REAL BUT DETAILS WRONG, DOI IS A DIFFERENT PAPER, NOT FOUND
    similarity: float
    reasons: list[str] = field(default_factory=list)
    match: Found | None = None


def normalise(text: str) -> str:
    """Lower case, letters and digits only, single spaces."""
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalise(a), normalise(b)).ratio()


def surname(name: str) -> str:
    return normalise(name).split()[-1] if normalise(name) else ""


def parse_citations(reply: str) -> list[Citation]:
    """Pull the JSON list out of the model's reply (models often add text or code fences around it)."""
    start, end = reply.find("["), reply.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        items = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        return []
    citations = []
    for item in items:
        if not isinstance(item, dict):
            continue
        authors = item.get("authors") or []
        year = item.get("year")
        citations.append(
            Citation(
                authors=[str(a) for a in authors]
                if isinstance(authors, list)
                else [str(authors)],
                year=int(year)
                if isinstance(year, int | float | str) and str(year).isdigit()
                else None,
                title=str(item.get("title") or ""),
                venue=str(item.get("venue") or ""),
                doi=str(item.get("doi") or "")
                .strip()
                .removeprefix("https://doi.org/")
                .removeprefix("doi:"),
            )
        )
    return citations


# ---------- the two public databases


def crossref_record(item: dict[str, Any]) -> Found:
    date_parts = (item.get("issued") or {}).get("date-parts") or [[None]]
    return Found(
        source="Crossref",
        title=(item.get("title") or [""])[0],
        year=date_parts[0][0],
        authors=[a.get("family", "") for a in item.get("author", [])],
        doi=item.get("DOI", ""),
    )


def crossref_by_doi(client: httpx.Client, doi: str) -> Found | None:
    response = client.get(f"https://api.crossref.org/works/{doi}")
    return (
        crossref_record(response.json()["message"])
        if response.status_code == 200
        else None
    )


def crossref_search(client: httpx.Client, title: str) -> list[Found]:
    response = client.get(
        "https://api.crossref.org/works",
        params={"query.bibliographic": title, "rows": 5},
    )
    return (
        [crossref_record(item) for item in response.json()["message"]["items"]]
        if response.status_code == 200
        else []
    )


def openalex_search(client: httpx.Client, title: str) -> list[Found]:
    response = client.get(
        "https://api.openalex.org/works", params={"search": title, "per-page": 5}
    )
    if response.status_code != 200:
        return []
    return [
        Found(
            source="OpenAlex",
            title=item.get("title") or "",
            year=item.get("publication_year"),
            authors=[
                (a["author"]["display_name"]).split()[-1]
                for a in item.get("authorships", [])
                if a.get("author")
            ],
            doi=(item.get("doi") or "").removeprefix("https://doi.org/"),
        )
        for item in response.json().get("results", [])
    ]


def verify(client: httpx.Client, citation: Citation) -> Verdict:
    if not citation.title.strip():
        return Verdict(citation, "NOT FOUND", 0.0, ["no title given"])
    doi_paper = crossref_by_doi(client, citation.doi) if citation.doi else None
    candidates = crossref_search(client, citation.title) + openalex_search(
        client, citation.title
    )
    best = max(
        candidates, key=lambda c: similarity(citation.title, c.title), default=None
    )
    best_similarity = similarity(citation.title, best.title) if best else 0.0

    if best and best_similarity >= TITLE_MATCH:
        reasons = []
        if citation.year and best.year and abs(citation.year - best.year) > 1:
            reasons.append(f"year: claimed {citation.year}, real {best.year}")
        claimed_first = surname(citation.authors[0]) if citation.authors else ""
        if claimed_first and claimed_first not in {surname(a) for a in best.authors}:
            reasons.append(
                f"first author {citation.authors[0]!r} is not among the real authors {best.authors[:4]}"
            )
        if citation.doi and doi_paper is None:
            reasons.append(f"the DOI {citation.doi} does not exist")
        elif (
            doi_paper is not None
            and similarity(citation.title, doi_paper.title) < TITLE_MATCH
        ):
            reasons.append(f"the DOI belongs to a different paper: {doi_paper.title!r}")
        return Verdict(
            citation,
            "REAL BUT DETAILS WRONG" if reasons else "REAL",
            best_similarity,
            reasons,
            best,
        )
    if doi_paper is not None:
        return Verdict(
            citation,
            "DOI IS A DIFFERENT PAPER",
            best_similarity,
            [f"the DOI belongs to {doi_paper.title!r} ({doi_paper.year})"],
            doi_paper,
        )
    reasons = ["no paper with a similar title in Crossref or OpenAlex"]
    if citation.doi:
        reasons.append(f"the DOI {citation.doi} does not exist")
    return Verdict(citation, "NOT FOUND", best_similarity, reasons, best)


# ---------- asking the models


def parse_spec(spec: str) -> tuple[str, str]:
    profile, _, explicit_model = spec.partition(":")
    if profile not in PROFILES:
        raise SystemExit(f"unknown profile {profile!r}; choose from {sorted(PROFILES)}")
    return profile, explicit_model or model_name(profile)


def ask(profile: str, model: str, prompt: str) -> str:
    client = make_openai_client(profile)
    return chat_messages(
        client,
        model,
        [{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2500,
    ).text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask models for citations and check whether they exist."
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, metavar="SPEC")
    parser.add_argument(
        "--prompts",
        nargs="+",
        choices=sorted(PROMPTS),
        default=sorted(PROMPTS, reverse=True),
    )
    args = parser.parse_args()

    print(f"Topic: {args.topic}\n")
    saved: list[dict[str, Any]] = []
    tally: list[list[str]] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as http:
        for spec in args.models:
            profile, model = parse_spec(spec)
            for prompt_name in args.prompts:
                label = f"{profile}:{model} / {prompt_name} prompt"
                print("=" * 100 + f"\n{label}\n" + "=" * 100)
                try:
                    reply = ask(
                        profile, model, PROMPTS[prompt_name].format(topic=args.topic)
                    )
                except MissingConfigError as error:
                    print(f"skipped: {error}\n")
                    continue
                citations = parse_citations(reply)
                if not citations:
                    print(
                        f"No citations could be read from the reply (empty list or not JSON):\n{reply[:300]!r}\n"
                    )
                verdicts = [verify(http, c) for c in citations]
                for number, v in enumerate(verdicts, 1):
                    c = v.citation
                    print(
                        f"\n  {number}. {', '.join(c.authors[:3])} ({c.year}). {c.title}. {c.venue}  DOI: {c.doi or '-'}"
                    )
                    print(
                        f"     -> {v.verdict}   (best title similarity {v.similarity:.2f})"
                    )
                    for reason in v.reasons:
                        print(f"        - {reason}")
                    if v.match and v.verdict in {"REAL", "REAL BUT DETAILS WRONG"}:
                        print(
                            f"        found in {v.match.source}: {v.match.title!r} ({v.match.year}) doi {v.match.doi or '-'}"
                        )
                counts = {
                    k: sum(v.verdict == k for v in verdicts)
                    for k in (
                        "REAL",
                        "REAL BUT DETAILS WRONG",
                        "DOI IS A DIFFERENT PAPER",
                        "NOT FOUND",
                    )
                }
                tally.append(
                    [
                        label,
                        str(len(verdicts)),
                        str(counts["REAL"]),
                        str(counts["REAL BUT DETAILS WRONG"]),
                        str(counts["DOI IS A DIFFERENT PAPER"] + counts["NOT FOUND"]),
                    ]
                )
                saved.append(
                    {
                        "model": f"{profile}:{model}",
                        "prompt": prompt_name,
                        "reply": reply,
                        "verdicts": [asdict(v) for v in verdicts],
                    }
                )

    print("\n" + "=" * 100 + "\nSUMMARY\n" + "=" * 100)
    header = ["model / prompt", "citations", "real", "real, details wrong", "invented"]
    widths = [max(len(r[i]) for r in [header, *tally]) for i in range(len(header))]
    for row in [header, *tally]:
        print(
            "  ".join(
                cell.ljust(w) if i == 0 else cell.rjust(w)
                for i, (cell, w) in enumerate(zip(row, widths, strict=True))
            )
        )

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(
        json.dumps({"topic": args.topic, "runs": saved}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nEverything (replies and verdicts) saved to results/{RESULTS_FILE.name}")


if __name__ == "__main__":
    main()
