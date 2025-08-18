import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, Optional

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


class StructuredPersonData(BaseModel):
    """Structured data extracted from research about a person."""
    
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    current_company: Optional[str] = None
    """Current company the person works at."""
    role: Optional[str] = None
    """Current job title/role."""
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
class OutputState:
    """Output state defines the structured data returned by the graph."""

    structured_data: StructuredPersonData
    "Structured person data extracted from research."
    
    reflection_notes: str
    "Analysis and reasoning from the reflection step."
    
    research_complete: bool
    "Whether the research process is considered complete."


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
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company the person works at",
        "role": "Current job title/role",
        "prior_companies": "List of previous companies the person has worked at"
    })
    "Schema defining the structure of information to extract"
    
    reflection_notes: str = field(default="")
    "Analysis and reasoning from the reflection step"
    
    should_continue_research: bool = field(default=True)
    "Whether additional research is needed based on reflection analysis"





