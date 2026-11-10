"""Dataset loading and reproducible negative-example generation."""

from __future__ import annotations

import random
import string
import tarfile
from pathlib import Path


ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").rstrip("\r\n")


def load_leaked_passwords(
    path: str | Path,
    limit: int = 50000,
    seed: int = 42,
    strategy: str = "reservoir",
) -> list[str]:
    """Load a reproducible sample from a text file or tar.gz archive.

    Reservoir sampling avoids the ranking bias created by taking only the first
    entries from password lists that are ordered by frequency.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")
    if limit < 100:
        raise ValueError("limit must be at least 100")

    if strategy not in {"head", "reservoir"}:
        raise ValueError("strategy must be 'head' or 'reservoir'")

    rng = random.Random(seed)

    def lines():
        if source.name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(source, "r:gz") as archive:
                member = next((m for m in archive.getmembers() if m.isfile() and m.name.endswith(".txt")), None)
                if member is None:
                    raise ValueError("Archive contains no .txt password file")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("Could not read password file from archive")
                for raw in stream:
                    yield _decode(raw)
        else:
            with source.open("rb") as stream:
                for raw in stream:
                    yield _decode(raw)

    passwords: list[str] = []
    valid_seen = 0
    for value in lines():
        if not 1 <= len(value) <= 64:
            continue
        if strategy == "head":
            passwords.append(value)
            if len(passwords) >= limit:
                break
            continue
        if len(passwords) < limit:
            passwords.append(value)
        else:
            replacement = rng.randint(0, valid_seen)
            if replacement < limit:
                passwords[replacement] = value
        valid_seen += 1

    passwords = list(dict.fromkeys(passwords))

    if len(passwords) < 100:
        raise ValueError("Dataset produced fewer than 100 valid unique passwords")
    return passwords


def generate_strong_passwords(count: int, seed: int = 42) -> list[str]:
    """Generate reproducible strong examples for the experimental negative class."""
    rng = random.Random(seed)
    generated: set[str] = set()
    while len(generated) < count:
        length = rng.randint(12, 24)
        required = [
            rng.choice(string.ascii_lowercase),
            rng.choice(string.ascii_uppercase),
            rng.choice(string.digits),
            rng.choice("!@#$%^&*()-_=+"),
        ]
        characters = required + [rng.choice(ALPHABET) for _ in range(length - len(required))]
        rng.shuffle(characters)
        generated.add("".join(characters))
    return sorted(generated)
