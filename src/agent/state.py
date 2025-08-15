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
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default="")
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default_factory=list)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_experience": "Total years of professional experience",
        "current_company": "Current company or organization",
        "role": "Current job title or position",
        "prior_companies": "List of previous companies worked at"
    })
    "Schema defining the information we want to extract about the person"
    
    # Reflection fields (added to support conditional edges)
    years_experience: Optional[int] = field(default=None)
    "Total years of professional experience"
    
    current_company: Optional[str] = field(default=None)
    "Current company or organization"
    
    role: Optional[str] = field(default=None)
    "Current job title or position"
    
    prior_companies: list[str] = field(default_factory=list)
    "List of previous companies worked at"
    
    satisfaction_score: float = field(default=0.0)
    "Score from 0-1 indicating how satisfied we are with the research completeness"
    
    missing_info: list[str] = field(default_factory=list)
    "List of information that is still missing or unclear"
    
    needs_more_research: bool = field(default=True)
    "Whether additional research is needed"
    
    reasoning: str = field(default="")
    "Reasoning for the satisfaction score and decision on whether to continue research"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the structured information extracted from research."""

    years_experience: Optional[int] = field(default=None)
    "Total years of professional experience"

    current_company: Optional[str] = field(default=None)
    "Current company or organization"

    role: Optional[str] = field(default=None)
    "Current job title or position"

    prior_companies: list[str] = field(default_factory=list)
    "List of previous companies worked at"

    satisfaction_score: float = field(default=0.0)
    "Score from 0-1 indicating how satisfied we are with the research completeness"

    missing_info: list[str] = field(default_factory=list)
    "List of information that is still missing or unclear"

    needs_more_research: bool = field(default=True)
    "Whether additional research is needed"

    reasoning: str = field(default="")
    "Reasoning for the satisfaction score and decision on whether to continue research"




