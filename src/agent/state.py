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
    """Output state containing structured information extracted from research."""
    
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    
    current_company: Optional[str] = None
    """Current company where the person works."""
    
    current_role: Optional[str] = None
    """Current job title or role."""
    
    prior_companies: Optional[list[str]] = None
    """List of previous companies the person has worked at."""
    
    research_complete: bool = False
    """Whether the research process is considered complete."""
    
    missing_information: Optional[list[str]] = None
    """List of information that is still missing or unclear."""
    
    reflection_reasoning: Optional[str] = None
    """Reasoning for whether research should continue or stop."""


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Overall state for the research workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": {
            "type": "integer",
            "description": "Total years of professional work experience"
        },
        "current_company": {
            "type": "string", 
            "description": "Name of the company where the person currently works"
        },
        "current_role": {
            "type": "string",
            "description": "Current job title or position"
        },
        "prior_companies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of previous companies the person has worked at"
        }
    })
    "Schema defining the structure for information extraction"
    
    research_complete: bool = field(default=False)
    "Flag indicating whether the research process is complete"
    
    structured_info: Optional[dict[str, Any]] = field(default=None)
    "Structured information extracted from research"
    
    missing_info: Optional[list[str]] = field(default=None)
    "List of missing or unclear information"
    
    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning from the reflection step about research completeness"




