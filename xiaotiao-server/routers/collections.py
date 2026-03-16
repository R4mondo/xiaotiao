"""Collections router — manage paper collections/groups."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db.database import get_db

router = APIRouter(prefix="/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str


@router.get("")
def list_collections(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM collections ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_collection(body: CollectionCreate, db=Depends(get_db)):
    cid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO collections (id, name) VALUES (?, ?)",
        (cid, body.name)
    )
    db.commit()
    return {"id": cid, "name": body.name, "created_at": datetime.utcnow().isoformat()}


@router.get("/{collection_id}/papers")
def get_collection_papers(collection_id: str, db=Depends(get_db)):
    rows = db.execute(
        """SELECT p.* FROM papers p
           JOIN collection_papers cp ON cp.paper_id = p.id
           WHERE cp.collection_id = ?
           ORDER BY cp.added_at DESC""",
        (collection_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{collection_id}/papers/{paper_id}")
def add_paper_to_collection(collection_id: str, paper_id: str, db=Depends(get_db)):
    # Check both exist
    coll = db.execute("SELECT id FROM collections WHERE id=?", (collection_id,)).fetchone()
    if not coll:
        raise HTTPException(404, "Collection not found")
    paper = db.execute("SELECT id FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not paper:
        raise HTTPException(404, "Paper not found")

    db.execute(
        "INSERT OR IGNORE INTO collection_papers (collection_id, paper_id) VALUES (?, ?)",
        (collection_id, paper_id)
    )
    db.commit()
    return {"status": "ok"}


@router.delete("/{collection_id}")
def delete_collection(collection_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM collections WHERE id=?", (collection_id,))
    db.commit()
    return {"status": "deleted"}
