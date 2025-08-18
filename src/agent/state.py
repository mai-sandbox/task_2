from dataclasses import dataclass, field
from typing import Any, Optional, Annotated, Literal
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


class CompanyExperience(BaseModel):
    """Structured data for a person's experience at a company."""
    
    company_name: Optional[str] = None
    """Name of the company."""
    role: Optional[str] = None
    """Role/title at the company."""
    duration: Optional[str] = None
    """Duration of employment (e.g., '2019-2022', '3 years')."""
    is_current: bool = False
    """Whether this is the current position."""


class StructuredPersonInfo(BaseModel):
    """Structured information extracted about a person."""
    
    name: Optional[str] = None
    """Full name of the person."""
    email: str
    """Email address of the person."""
    current_company: Optional[str] = None
    """Current company where the person works."""
    current_role: Optional[str] = None
    """Current job title/role."""
    years_of_experience: Optional[int] = None
    """Total years of professional experience."""
    prior_companies: list[CompanyExperience] = []
    """List of prior companies and roles."""
    linkedin_url: Optional[str] = None
    """LinkedIn profile URL."""
    additional_info: Optional[str] = None
    """Any other relevant information."""


class ReflectionOutput(BaseModel):
    """Output from the reflection step."""
    
    structured_info: StructuredPersonInfo
    """Extracted structured information."""
    is_satisfactory: bool
    """Whether the extracted information is satisfactory."""
    missing_info: list[str] = []
    """List of missing information that should be searched."""
    reasoning: str
    """Reasoning for the decision to redo or not."""
    should_retry: bool
    """Whether to retry the search process."""


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
    
    structured_info: Optional[StructuredPersonInfo] = field(default=None)
    "Structured information extracted from research notes."
    
    reflection_output: Optional[ReflectionOutput] = field(default=None)
    "Output from the reflection step."
    
    retry_count: int = field(default=0)
    "Number of retries performed."
    
    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "years_of_experience": "Total years of professional experience",
        "current_company": "Current company where the person works",
        "current_role": "Current job title/role",
        "prior_companies": "List of previous companies and roles with durations",
        "education": "Educational background",
        "skills": "Key skills and expertise areas"
    })
    "Schema for information extraction."


@dataclass(kw_only=True)
class OutputState:
    """Output state returned to the user."""
    
    structured_info: StructuredPersonInfo
    "Final structured information about the person."
    
    raw_notes: str
    "Raw research notes collected."
    
    completeness_assessment: str
    "Assessment of information completeness."
