"""Only team-authored sample material is bundled; never overwrite admin revisions."""
import json
from uuid import uuid5, NAMESPACE_URL
from .config import ROOT
from .models import RagDocument
from .rag import Metadata, create


def seed_rag(db):
    for sample in json.loads((ROOT / "fixtures/rag_demo_corpus.json").read_text(encoding="utf-8")):
        document_id = uuid5(NAMESPACE_URL, "demo-rag-seed:" + sample["slug"])
        if db.get(RagDocument, document_id): continue
        meta = Metadata(**{key: value for key, value in sample.items() if key not in ("slug", "content")})
        raw = sample["content"].encode("utf-8")
        create(db, meta, [{"page": 1, "text": sample["content"]}], raw, sample["slug"] + ".txt",
               "text/plain; charset=utf-8", "AUTHORED_TEXT", None, document_id=document_id, published=True)
