from dataclasses import dataclass, field
from typing import Any, Optional, Annotated
import operator

from pydantic import BaseModel


@dataclass(kw_only=True)
class OutputState:
    """Output state returned to the user after research completion."""
    
    structured_info: dict[str, Any]
    "Structured information extracted about the person"
    
    research_complete: bool
    "Whether the research process is complete"
    
    reflection_reasoning: str
    "Final reasoning for the research decision"

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
    
    extraction_schema: Optional[dict[str, Any]] = field(default=None)
    "Schema defining what information to extract about the person"


@dataclass(kw_only=True)
class OverallState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    extraction_schema: dict[str, Any] = field(default_factory=dict)
    "Schema defining what information to extract about the person"
    
    structured_info: Optional[dict[str, Any]] = field(default=None)
    "Structured information extracted through reflection"
    
    reflection_decision: Optional[str] = field(default=None)
    "Decision whether to continue research or stop"
    
    reflection_reasoning: Optional[str] = field(default=None)
    "Reasoning behind the reflection decision"
    
    missing_information: list[str] = field(default_factory=list)
    "List of information that is missing and should be searched for"
    
    research_complete: bool = field(default=False)
    "Whether the research is considered complete"
