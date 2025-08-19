from dataclasses import dataclass, field
from typing import Any, Optional, Annotated
import operator

from pydantic import BaseModel, Field

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


class PersonProfile(BaseModel):
    """Structured profile information extracted from research notes."""
    
    years_experience: Optional[int] = Field(
        default=None,
        description="Total years of professional experience"
    )
    current_company: Optional[str] = Field(
        default=None,
        description="Current company the person works at"
    )
    role: Optional[str] = Field(
        default=None,
        description="Current job title or role"
    )
    prior_companies: list[str] = Field(
        default_factory=list,
        description="List of previous companies the person has worked at"
    )


class ReflectionDecision(BaseModel):
    """Decision model for reflection step evaluation."""
    
    is_satisfactory: bool = Field(
        description="Whether the current research is satisfactory"
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description="List of missing information that should be researched"
    )
    should_redo: bool = Field(
        description="Whether the research process should be redone"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the decision"
    )


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

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"


