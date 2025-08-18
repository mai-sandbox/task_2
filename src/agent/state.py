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


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OverallState:
    """Overall state that tracks the entire research process."""

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
        "years_experience": "Total years of professional experience",
        "current_company": "Current employer/company name",
        "role": "Current job title/position",
        "prior_companies": "List of previous companies worked at"
    })
    "Schema defining the structured information to extract about the person"
    
    reflection_decision: Optional[str] = field(default=None)
    "Decision from reflection: 'continue' to research more or 'stop' if satisfactory"
    
    years_experience: Optional[str] = field(default=None)
    "Extracted years of experience from reflection"
    
    current_company: Optional[str] = field(default=None)
    "Extracted current company from reflection"
    
    role: Optional[str] = field(default=None)
    "Extracted role from reflection"
    
    prior_companies: List[str] = field(default_factory=list)
    "Extracted list of prior companies from reflection"
    
    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning from reflection about information completeness"


@dataclass(kw_only=True)
class OutputState:
    """Output state containing the structured information extracted from research."""
    
    years_experience: Optional[str] = field(default=None)
    "Total years of professional experience of the person"
    
    current_company: Optional[str] = field(default=None)
    "Current employer/company name where the person works"
    
    role: Optional[str] = field(default=None)
    "Current job title/position of the person"
    
    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"
    
    completed_notes: List[str] = field(default_factory=list)
    "All research notes gathered during the process"
    
    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning from the reflection step about information completeness"





