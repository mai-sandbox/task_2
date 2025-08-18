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

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company name",
        "current_role": "Current job title/role",
        "prior_companies": "List of previous companies worked at with roles and approximate years",
        "education": "Educational background if available",
        "skills": "Key professional skills mentioned"
    })
    "Schema defining what information to extract about the person"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    reflection_result: Optional[str] = field(default=None)
    "Result of the reflection step analyzing research quality and completeness"
    
    should_continue_research: bool = field(default=True)
    "Whether to continue research based on reflection assessment"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines what the graph returns to the user."""

    completed_notes: list[str]
    "All research notes collected about the person"
    
    reflection_result: str
    "Final reflection assessment of the research quality and extracted information"
