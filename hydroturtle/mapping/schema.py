from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

ValueSpec = Union[str, Dict[str, Any]]  # str or {"value":...} or {"map":...} etc.

@dataclass
class Rule:
    when_columns: List[str]
    subject: Optional[str]
    triples: List[List[ValueSpec]]

@dataclass
class Mapping:
    prefixes: Dict[str, str]
    id_subject_template: str
    rules: List[Rule]
