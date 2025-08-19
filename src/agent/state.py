"""State module for the people research agent."""

import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional

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


class ExtractedInfo(BaseModel):
    """Structured information extracted about a person's professional background."""
    
    years_experience: Optional[int] = None
    """Total years of professional experience."""
    current_company: Optional[str] = None
    """Current company where the person works."""
    role: Optional[str] = None
    """Current role or job title."""
    prior_companies: List[str] = []
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
    """Overall state that tracks the complete research process."""

    person: Person
    "Person to research provided by the user."

    user_notes: Optional[str] = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default_factory=list)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_experience": "Total years of professional experience",
        "current_company": "Current company where the person works",
        "role": "Current role or job title",
        "prior_companies": "List of previous companies the person has worked at"
    })
    "Schema defining the information to extract about the person"
    
    extracted_info: Optional[ExtractedInfo] = field(default=None)
    "Structured information extracted from research notes"
    
    reflection_decision: Optional[str] = field(default=None)
    "Decision from reflection: 'continue' or 'complete'"


@dataclass(kw_only=True)
class OutputState:
    """Output state containing the final structured information about the person."""
    
    person: Person
    "Original person information provided as input"
    
    extracted_info: ExtractedInfo
    "Structured professional information extracted from research"
    
    years_experience: Optional[int] = field(default=None)
    "Total years of professional experience"
    
    current_company: Optional[str] = field(default=None)
    "Current company where the person works"
    
    role: Optional[str] = field(default=None)
    "Current role or job title"
    
    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"
    
    research_notes: str = field(default="")
    "Consolidated research notes from all searches"






