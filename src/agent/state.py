import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional

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


class StructuredPersonInfo(BaseModel):
    """Structured information about a person extracted from research notes."""
    
    name: Optional[str] = None
    """The full name of the person."""
    
    current_company: Optional[str] = None
    """The current company where the person works."""
    
    current_role: Optional[str] = None
    """The current job title/role of the person."""
    
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    
    prior_companies: List[str] = field(default_factory=list)
    """List of previous companies the person has worked at."""
    
    skills: List[str] = field(default_factory=list)
    """List of professional skills mentioned."""
    
    education: Optional[str] = None
    """Educational background information."""


class ReflectionResult(BaseModel):
    """Result of the reflection step."""
    
    structured_info: StructuredPersonInfo
    """Structured information extracted from notes."""
    
    is_satisfactory: bool
    """Whether the information gathered is sufficient."""
    
    missing_information: List[str] = field(default_factory=list)
    """List of missing key information that should be searched."""
    
    additional_search_queries: List[str] = field(default_factory=list)
    """Suggested additional search queries to gather missing information."""
    
    reasoning: str
    """Reasoning for the evaluation and decision to redo or not."""
    
    should_redo_search: bool
    """Whether to perform additional search based on the evaluation."""


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

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "name": "Full name of the person",
        "current_company": "Current company where the person works",
        "current_role": "Current job title or role",
        "years_of_experience": "Total years of professional experience",
        "prior_companies": "List of previous companies worked at",
        "skills": "Professional skills and expertise",
        "education": "Educational background"
    })
    "Schema defining what information to extract"

    search_queries: list[str] = field(default_factory=list)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"

    reflection_result: Optional[ReflectionResult] = field(default=None)
    "Result of the reflection step"

    search_iteration: int = field(default=0)
    "Current search iteration count"

    max_search_iterations: int = field(default=2)
    "Maximum number of search iterations allowed"


@dataclass(kw_only=True)
class OutputState:
    """Output state returned to the user."""
    
    structured_info: StructuredPersonInfo
    "Structured information about the person"
    
    reflection_result: ReflectionResult
    "Final reflection result with evaluation"
    
    all_notes: str
    "All research notes collected"
