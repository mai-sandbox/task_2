import operator
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional

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
            "prior_companies": "List of previous companies worked at",
            "education": "Educational background and qualifications",
            "skills": "Key technical and professional skills",
            "notable_achievements": "Significant accomplishments or projects",
        }
    )
    "Schema defining the structured information to extract about the person"

    # Fields populated by reflection node
    completeness_assessment: Optional[ResearchCompleteness] = field(default=None)
    "Assessment of the research completeness from reflection"

    years_of_experience: Optional[int] = field(default=None)
    "Total years of professional experience extracted from research"

    current_company: Optional[str] = field(default=None)
    "Current employer/company extracted from research"

    current_role: Optional[str] = field(default=None)
    "Current job title or position extracted from research"

    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies extracted from research"

    education: Optional[str] = field(default=None)
    "Educational background extracted from research"

    skills: List[str] = field(default_factory=list)
    "Key skills extracted from research"

    notable_achievements: List[str] = field(default_factory=list)
    "Notable achievements extracted from research"

    raw_notes: str = field(default="")
    "Consolidated raw notes from all research iterations"

    research_iterations: int = field(default=0)
    "Number of research iterations performed"


class ResearchCompleteness(BaseModel):
    """Assessment of research completeness and quality."""

    is_complete: bool = Field(
        description="Whether the research gathered all essential information"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="List of missing information that should be searched",
    )
    confidence_score: float = Field(
        default=0.0, description="Confidence score of the research completeness (0-1)"
    )
    reasoning: str = Field(
        description="Reasoning for the completeness assessment and decision to continue or finish"
    )
    suggested_queries: List[str] = Field(
        default_factory=list,
        description="Suggested search queries if more research is needed",
    )


@dataclass(kw_only=True)
class OutputState:
    """Output state containing the final structured research results."""

    # Core information about the person
    years_of_experience: Optional[int] = field(default=None)
    "Total years of professional experience"

    current_company: Optional[str] = field(default=None)
    "Name of the current employer/company"

    current_role: Optional[str] = field(default=None)
    "Current job title or position"

    prior_companies: List[str] = field(default_factory=list)
    "List of previous companies the person has worked at"

    # Additional extracted information
    education: Optional[str] = field(default=None)
    "Educational background and qualifications"

    skills: List[str] = field(default_factory=list)
    "Key technical and professional skills"

    notable_achievements: List[str] = field(default_factory=list)
    "Significant accomplishments or projects"

    # Research metadata
    completeness_assessment: Optional[ResearchCompleteness] = field(default=None)
    "Assessment of the research completeness and quality"

    raw_notes: str = field(default="")
    "Consolidated raw notes from all research iterations"

    research_iterations: int = field(default=0)
    "Number of research iterations performed"
