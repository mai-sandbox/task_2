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


class OutputState(BaseModel):
    """Structured output state for person research results."""
    
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    
    current_company: Optional[str] = None
    """Current company where the person works."""
    
    role: Optional[str] = None
    """Current job title or role."""
    
    prior_companies: Optional[List[str]] = None
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
    """Overall state defines the complete state for the research workflow."""

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
        "years_of_experience": {
            "type": "integer",
            "description": "Total years of professional experience",
            "required": True
        },
        "current_company": {
            "type": "string", 
            "description": "Current company where the person works",
            "required": True
        },
        "role": {
            "type": "string",
            "description": "Current job title or role", 
            "required": True
        },
        "prior_companies": {
            "type": "array",
            "description": "List of previous companies the person has worked at",
            "items": {"type": "string"},
            "required": True
        }
    })
    "Schema defining the structured format for person research data"
    
    # Reflection workflow fields
    reflection_result: Any = field(default=None)
    "Complete reflection evaluation result from the reflection node"
    
    reflection_decision: Optional[str] = field(default=None)
    "Decision from reflection: SATISFACTORY, CONTINUE, or REDO"
    
    extracted_data: dict[str, Any] = field(default_factory=dict)
    "Structured data extracted from research notes according to schema"




