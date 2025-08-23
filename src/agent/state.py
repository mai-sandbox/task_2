from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, List, Dict
import operator

from pydantic import BaseModel

class Person(BaseModel):
    """A class representing a person to research."""

    name: Optional[str] = None
    """The name of the person."""
    company: Optional[str] = None
    """The current company of the person."""
    linkedin: Optional[str] = None
    """The Linkedin URL of the person."""
    email: str
    """The email of the person."""
    role: Optional[str] = None
    """The current title of the person."""


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OutputState:
    """Output state containing structured professional information extracted from research."""
    
    years_experience: Optional[int] = field(default=None)
    "Total years of professional experience"
    
    current_company: Optional[str] = field(default=None)
    "Current company where the person works"
    
    current_role: Optional[str] = field(default=None)
    "Current job title or role"
    
    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"
    
    reflection_notes: str = field(default="")
    "Notes from the reflection process about completeness and quality of information"
    
    satisfaction_score: float = field(default=0.0)
    "Score from 0-1 indicating how satisfied we are with the completeness of information"


@dataclass(kw_only=True)
class OverallState:
    """Overall state that tracks the entire research and reflection process."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."
    
    extraction_schema: Dict[str, Any] = field(default_factory=lambda: {
        "years_experience": "Total years of professional experience (integer)",
        "current_company": "Name of the current company where the person works",
        "current_role": "Current job title or position",
        "prior_companies": "List of previous companies the person has worked at",
        "education": "Educational background including degrees and institutions",
        "skills": "Key professional skills and expertise areas",
        "notable_achievements": "Significant career achievements or recognitions"
    })
    "Schema defining what information to extract about the person"

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    # Fields for reflection output
    years_experience: Optional[int] = field(default=None)
    "Total years of professional experience"
    
    current_company: Optional[str] = field(default=None)
    "Current company where the person works"
    
    current_role: Optional[str] = field(default=None)
    "Current job title or role"
    
    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"
    
    reflection_notes: str = field(default="")
    "Notes from the reflection process about completeness and quality of information"
    
    satisfaction_score: float = field(default=0.0)
    "Score from 0-1 indicating how satisfied we are with the completeness of information"
    
    decision: Optional[str] = field(default=None)
    "Decision from reflection: 'continue' to research more or 'complete' to finish"



