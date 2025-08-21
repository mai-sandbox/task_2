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

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    # Add default values for required fields
    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"

    reflection_result: Optional[Any] = field(default=None)
    "Structured reflection result containing extracted professional information"

    search_iteration: int = field(default=0)
    "Counter for search iterations to prevent infinite loops"

    extraction_schema: Optional[dict[str, Any]] = field(default=None)
    "Schema defining what information to extract about the person"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final result returned to the user."""

    person: Person
    "The researched person"

    reflection_result: Optional[Any] = field(default=None)
    "Final structured professional information about the person"

    completed_notes: list[str] = field(default_factory=list)
    "All research notes collected during the process"

    total_iterations: int = field(default=0)
    "Total number of search iterations performed"
