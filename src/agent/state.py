import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel


class WorkExperienceEntry(BaseModel):
    """A single work experience entry."""
    
    company: str
    """The company name."""
    role: str
    """The role/title at the company."""
    start_date: Optional[str] = None
    """Start date (if available)."""
    end_date: Optional[str] = None
    """End date (if available), 'Present' for current role."""
    duration: Optional[str] = None
    """Duration at the company (e.g., '2 years', '1.5 years')."""


class StructuredPersonInfo(BaseModel):
    """Structured format for key person information."""
    
    years_of_experience: Optional[str] = None
    """Total years of professional experience."""
    current_company: Optional[str] = None
    """Current company name."""
    current_role: Optional[str] = None
    """Current role/title."""
    prior_companies: list[WorkExperienceEntry] = []
    """List of previous work experiences."""
    education: Optional[str] = None
    """Educational background if available."""
    skills: list[str] = []
    """Key skills or technologies mentioned."""
    location: Optional[str] = None
    """Current location if available."""


class ReflectionDecision(str, Enum):
    """Decision outcomes for reflection step."""
    COMPLETE = "complete"
    SEARCH_MORE = "search_more"


class ReflectionResult(BaseModel):
    """Result of the reflection step."""
    
    structured_info: StructuredPersonInfo
    """The structured information extracted from notes."""
    decision: ReflectionDecision
    """Whether the information is complete or more search is needed."""
    missing_info: list[str] = []
    """List of missing information types."""
    additional_queries: list[str] = []
    """Additional search queries to fill gaps if decision is SEARCH_MORE."""
    reasoning: str
    """Reasoning for the decision."""
    completeness_score: float
    """Score from 0-1 indicating how complete the information is."""


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
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company name",
        "current_role": "Current role/title",
        "prior_companies": "List of previous companies with roles and durations",
        "education": "Educational background",
        "skills": "Key skills and technologies",
        "location": "Current location"
    })
    "Schema defining what information to extract about the person"
    
    reflection_result: Optional[ReflectionResult] = field(default=None)
    "Result of the reflection step with structured info and decision"
    
    iteration_count: int = field(default=0)
    "Number of research iterations performed"


@dataclass(kw_only=True)
class OutputState:
    """Output state defines what is returned to the user."""
    
    structured_info: StructuredPersonInfo
    "The final structured information about the person"
    
    all_notes: str
    "All research notes compiled together"
    
    final_reasoning: str
    "Final reasoning about the research completeness"
