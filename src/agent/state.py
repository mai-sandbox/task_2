from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, List
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


class PersonInfo(BaseModel):
    """Structured information about a person's professional background."""
    
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    
    current_company: Optional[str] = None
    """The company where the person currently works."""
    
    role: Optional[str] = None
    """Current job title or role."""
    
    prior_companies: List[str] = []
    """List of companies the person has previously worked at."""


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Overall state for the research agent workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: Optional[str] = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "The company where the person currently works",
        "role": "Current job title or role",
        "prior_companies": "List of companies the person has previously worked at"
    })
    "Schema defining what information to extract about the person"
    
    structured_info: Optional[PersonInfo] = field(default=None)
    "Structured information extracted from research notes"
    
    continue_research: bool = field(default=True)
    "Whether to continue researching or finish"


@dataclass(kw_only=True)
class OutputState:
    """Output state containing the final structured information about the person."""
    
    person_info: PersonInfo
    "Structured information about the person's professional background"
    
    research_notes: str
    "Consolidated research notes from all searches"
    
    completeness_assessment: str
    "Assessment of how complete the gathered information is"



