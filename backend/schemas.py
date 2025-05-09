from typing import Optional, List, Any, Dict

from pydantic import BaseModel


class Filters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    campaigns: Optional[List[int]] = None
    detail_level: Optional[str] = None