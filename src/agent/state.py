"""State definitions for the people research agent."""

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

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {
            "years_of_experience": "Total years of professional experience",
            "current_company": "Name of the current employer/company",
            "current_role": "Current job title or position",
            "prior_companies": "List of previous companies worked at with roles and duration if available",
            "education": "Educational background including degrees and institutions",
            "skills": "Key technical and professional skills",
            "notable_achievements": "Significant accomplishments, projects, or recognition",
        }
    )
    "Schema defining the structured format for extracting person information"

    structured_info: Optional["PersonInfo"] = field(default=None)
    "Structured information extracted from research notes"

    reflection_result: Optional["ReflectionResult"] = field(default=None)
    "Result of the reflection process evaluating research completeness"

    research_iterations: int = field(default=0)
    "Number of research iterations performed"

    should_continue: Optional[str] = field(default=None)
    "Decision from reflection: 'continue' or 'end'"


class PersonInfo(BaseModel):
    """Structured information about a person extracted from research."""

    years_of_experience: Optional[int] = None
    """Total years of professional experience."""

    current_company: Optional[str] = None
    """Name of the current employer/company."""

    current_role: Optional[str] = None
    """Current job title or position."""

    prior_companies: Optional[List[dict]] = None
    """List of previous companies with roles and duration."""

    education: Optional[List[str]] = None
    """Educational background including degrees and institutions."""

    skills: Optional[List[str]] = None
    """Key technical and professional skills."""

    notable_achievements: Optional[List[str]] = None
    """Significant accomplishments, projects, or recognition."""


class ReflectionResult(BaseModel):
    """Result of the reflection process on research completeness."""

    is_satisfactory: bool
    """Whether the research gathered sufficient information."""

    missing_information: List[str]
    """List of information that is still missing or incomplete."""

    additional_search_suggestions: Optional[List[str]] = None
    """Suggestions for additional searches if needed."""

    reasoning: str
    """Detailed reasoning for the decision to continue or redo research."""

    confidence_score: float
    """Confidence score (0-1) in the completeness of the research."""


@dataclass(kw_only=True)
class OutputState:
    """Output state defines the final results of the research process."""

    person: Person
    """Original person information provided as input."""

    structured_info: PersonInfo
    """Structured information extracted from research."""

    reflection: ReflectionResult
    """Results of the reflection process."""

    raw_notes: List[str]
    """Raw research notes collected during the process."""

    research_iterations: int = field(default=1)
    """Number of research iterations performed."""
