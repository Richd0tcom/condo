from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProcessingResult:
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_after_seconds: Optional[int] = None
