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
class OutputState:
    """Output state containing structured information extracted from research."""

    years_of_experience: Optional[int] = field(default=None)
    "Total years of professional experience."

    current_company: Optional[str] = field(default=None)
    "The current company where the person works."

    role: Optional[str] = field(default=None)
    "The current role or job title of the person."

    prior_companies: list[str] = field(default_factory=list)
    "List of companies the person has previously worked at."


@dataclass(kw_only=True)
class OverallState:
    """Overall state that manages the entire research workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {
            "years_of_experience": "Total years of professional experience",
            "current_company": "Current company where the person works",
            "role": "Current role or job title",
            "prior_companies": "List of previous companies worked at",
        }
    )
    "Schema defining what information to extract from research notes."

    # Reflection output fields
    years_of_experience: Optional[int] = field(default=None)
    "Extracted years of professional experience."

    current_company: Optional[str] = field(default=None)
    "Extracted current company."

    role: Optional[str] = field(default=None)
    "Extracted current role."

    prior_companies: list[str] = field(default_factory=list)
    "Extracted list of prior companies."

    # Internal fields for routing decisions
    _continue_research: Optional[bool] = field(default=None)
    "Internal flag for whether to continue research."

    _reflection_reasoning: Optional[str] = field(default=None)
    "Internal reasoning for the reflection decision."

    _missing_information: list[str] = field(default_factory=list)
    "Internal list of missing information identified during reflection."
