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


class WorkExperience(BaseModel):
    """A structured representation of work experience."""
    
    company: str = Field(description="Name of the company")
    role: str = Field(description="Job title/role at the company") 
    start_date: Optional[str] = Field(description="Start date (approximate if exact date unknown)")
    end_date: Optional[str] = Field(description="End date ('Present' or 'Current' if still working)")
    duration: Optional[str] = Field(description="Duration at the company")


class PersonInformation(BaseModel):
    """Structured information about a person."""
    
    name: Optional[str] = Field(description="Full name of the person")
    current_company: Optional[str] = Field(description="Current company where the person works")
    current_role: Optional[str] = Field(description="Current job title/role")
    years_of_experience: Optional[int] = Field(description="Total years of professional experience")
    prior_companies: List[WorkExperience] = Field(default_factory=list, description="List of previous work experiences")
    linkedin_url: Optional[str] = Field(description="LinkedIn profile URL")
    email: Optional[str] = Field(description="Email address")


class ReflectionResult(BaseModel):
    """Result of the reflection step."""
    
    structured_information: PersonInformation = Field(description="Structured information about the person")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0 on completeness of information")
    missing_information: List[str] = Field(default_factory=list, description="List of missing information that should be searched for")
    additional_queries: List[str] = Field(default_factory=list, description="Additional search queries to fill gaps")
    should_continue_research: bool = Field(description="Whether more research is needed")
    reasoning: str = Field(description="Reasoning for the decision to continue or stop research")


@dataclass(kw_only=True)
class InputState:
    """Input state defines the interface between the graph and the user (external API)."""

    person: Person
    "Person to research."

    user_notes: Optional[dict[str, Any]] = field(default=None)
    "Any notes from the user to start the research process."


@dataclass(kw_only=True)
class OutputState:
    """Output state defines what the graph returns to the user."""
    
    person_information: Optional[PersonInformation] = field(default=None)
    "Structured information extracted about the person."
    
    reflection_results: Optional[ReflectionResult] = field(default=None)
    "Results from the reflection step."
    
    raw_notes: Optional[str] = field(default=None)
    "Raw research notes combined."


@dataclass(kw_only=True)
class OverallState:
    """Overall state for the research graph workflow."""

    person: Person
    "Person to research provided by the user."

    user_notes: str = field(default=None)
    "Any notes from the user to start the research process."

    extraction_schema: dict[str, Any] = field(default_factory=lambda: {
        "name": "Full name of the person",
        "current_company": "Current company where the person works", 
        "current_role": "Current job title/role",
        "years_of_experience": "Total years of professional experience",
        "prior_companies": "List of previous companies and roles with dates",
        "linkedin_url": "LinkedIn profile URL",
        "email": "Email address"
    })
    "Schema defining what information to extract about the person."

    search_queries: list[str] = field(default=None)
    "List of generated search queries to find relevant information"

    completed_notes: Annotated[list, operator.add] = field(default_factory=list)
    "Notes from completed research related to the schema"
    
    reflection_result: Optional[ReflectionResult] = field(default=None)
    "Result from the reflection step."
    
    person_information: Optional[PersonInformation] = field(default=None)
    "Structured information extracted about the person."
    
    research_iterations: int = field(default=0)
    "Number of research iterations completed."
