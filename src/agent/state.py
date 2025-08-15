from dataclasses import dataclass, field
from typing import Any, Optional, Annotated
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


class OutputState(BaseModel):
    """Structured output state containing extracted information about a person."""
    
    years_experience: Optional[int] = None
    """Total years of professional experience."""
    
    current_company: Optional[str] = None
    """Current company where the person works."""
    
    current_role: Optional[str] = None
    """Current job title or role."""
    
    prior_companies: list[str] = []
    """List of previous companies the person has worked at."""


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Overall state that manages the complete research workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_experience": "Total years of professional experience",
        "current_company": "Current company where the person works",
        "current_role": "Current job title or role",
        "prior_companies": "List of previous companies the person has worked at"
    })
    "Schema defining the information we want to extract about the person"
    
    reflection_decision: Optional[Any] = field(default=None)
    "Decision from the reflection step about whether to continue research"




