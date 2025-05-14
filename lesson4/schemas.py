
from pydantic import BaseModel
from typing import List, Optional

class ReviewRow(BaseModel):
    review: str               # the raw user feedback
    label: str                # "bug" | "feature"  – ground-truth for eval
    known_issues: Optional[List[str]] = None   # short summaries of existing bugs
    is_duplicate: Optional[bool] = None        # ground-truth for duplicate check
