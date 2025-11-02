"""Document retrieval service backed by Postgres."""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn

router = APIRouter()

class DocPara(BaseModel):
    doc_id: str
    para_id: str
    text: str
    page: Optional[int] = None
    ref: Optional[str] = None

class DocsRequest(BaseModel):
    para_ids: List[str]

@router.post("/get", response_model=List[DocPara])
async def get_docs(req: DocsRequest):
    """Retrieve document paragraphs by para_id.
    Accepts numeric para IDs (policy_para.id as string), or para_ref; returns best match.
    """
    out: List[DocPara] = []
    with get_conn() as conn:
        for pid in req.para_ids:
            row = None
            try:
                as_int = int(pid)
            except ValueError:
                # Lookup by para_ref (first match)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT p.doc_id, pp.id, pp.para_ref, pp.text, pp.page
                        FROM policy_para pp
                        JOIN policy p ON p.id = pp.policy_id
                        WHERE pp.para_ref = %s
                        LIMIT 1
                        """,
                        (pid,),
                    )
                    row = cur.fetchone()
            else:
                with get_conn() as _:
                    pass
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT p.doc_id, pp.id, pp.para_ref, pp.text, pp.page
                        FROM policy_para pp
                        JOIN policy p ON p.id = pp.policy_id
                        WHERE pp.id = %s
                        """,
                        (as_int,),
                    )
                    row = cur.fetchone()
            if row:
                doc_id, para_pk, para_ref, text, page = row
                out.append(DocPara(doc_id=str(doc_id), para_id=str(para_pk), text=text, page=page, ref=para_ref))
    return out
