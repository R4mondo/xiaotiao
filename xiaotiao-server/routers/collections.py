"""合集路由：管理论文合集/分组。"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db.database import get_db

router = APIRouter(prefix="/collections", tags=["合集"])


class CollectionCreate(BaseModel):
    name: str


@router.get(
    "",
    summary="获取合集列表",
    description="返回所有合集。",
)
def list_collections(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM collections ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.post(
    "",
    summary="创建合集",
    description="创建一个新的论文合集。",
)
def create_collection(body: CollectionCreate, db=Depends(get_db)):
    cid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO collections (id, name) VALUES (?, ?)",
        (cid, body.name)
    )
    db.commit()
    return {"id": cid, "name": body.name, "created_at": datetime.utcnow().isoformat()}


@router.get(
    "/{collection_id}/papers",
    summary="获取合集内论文",
    description="返回指定合集内的论文列表。",
)
def get_collection_papers(collection_id: str, db=Depends(get_db)):
    rows = db.execute(
        """SELECT p.* FROM papers p
           JOIN collection_papers cp ON cp.paper_id = p.id
           WHERE cp.collection_id = ?
           ORDER BY cp.added_at DESC""",
        (collection_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post(
    "/{collection_id}/papers/{paper_id}",
    summary="添加论文到合集",
    description="将论文加入指定合集。",
)
def add_paper_to_collection(collection_id: str, paper_id: str, db=Depends(get_db)):
    # Check both exist
    coll = db.execute("SELECT id FROM collections WHERE id=?", (collection_id,)).fetchone()
    if not coll:
        raise HTTPException(404, "未找到该合集。")
    paper = db.execute("SELECT id FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not paper:
        raise HTTPException(404, "未找到该论文。")

    db.execute(
        "INSERT OR IGNORE INTO collection_papers (collection_id, paper_id) VALUES (?, ?)",
        (collection_id, paper_id)
    )
    db.commit()
    return {"status": "ok"}


@router.delete(
    "/{collection_id}",
    summary="删除合集",
    description="删除指定合集。",
)
def delete_collection(collection_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM collections WHERE id=?", (collection_id,))
    db.commit()
    return {"status": "deleted"}
