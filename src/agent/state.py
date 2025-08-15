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


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the structured results of the research process."""

    years_of_experience: Optional[int] = field(default=None)
    """Total years of professional experience."""
    
    current_company: Optional[str] = field(default=None)
    """Current company where the person works."""
    
    role: Optional[str] = field(default=None)
    """Current job title/role of the person."""
    
    prior_companies: list[str] = field(default_factory=list)
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
    """Overall state defines the complete state used throughout the graph execution."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company where the person works",
        "role": "Current job title/role of the person",
        "prior_companies": "List of previous companies the person has worked at"
    })
    "Schema defining the information to extract during research"




