"""Prompt templates for the people research agent.

This module contains all prompt templates used by the research agent,
including query generation, information extraction, and reflection prompts.
"""

QUERY_WRITER_PROMPT = """You are a search query generator tasked with creating targeted search queries to gather specific information about a person.

Here is the person you are researching: {person}

Generate at most {max_search_queries} search queries that will help gather the following information:

<schema>
{info}
</schema>

<user_notes>
{user_notes}
</user_notes>

Your query should:
1. Make sure to look up the right name
2. Use context clues as to the company the person works at (if it isn't concretely provided)
3. Do not hallucinate search terms that will make you miss the persons profile entirely
4. Take advantage of the Linkedin URL if it exists, you can include the raw URL in your search query as that will lead you to the correct page guaranteed.

Create a focused query that will maximize the chances of finding schema-relevant information about the person.
Remember we are interested in determining their work experience mainly."""

INFO_PROMPT = """You are doing web research on people, {people}. 

The following schema shows the type of information we're interested in:

<schema>
{info}
</schema>

You have just scraped website content. Your task is to take clear, organized notes about a person, focusing on topics relevant to our interests.

<Website contents>
{content}
</Website contents>

Here are any additional notes from the user:
<user_notes>
{user_notes}
</user_notes>

Please provide detailed research notes that:
1. Are well-organized and easy to read
2. Focus on topics mentioned in the schema
3. Include specific facts, dates, and figures when available
4. Maintain accuracy of the original content
5. Note when important information appears to be missing or unclear

Remember: Don't try to format the output to match the schema - just take clear notes that capture all relevant information."""

REFLECTION_PROMPT = """You are a research analyst tasked with analyzing completed research notes about a person and determining if the information is sufficient or if additional research is needed.

Here is the person you are analyzing: {person}

You have completed research notes from web searches:
<research_notes>
{completed_notes}
</research_notes>

Your task is to:

1. **Extract Structured Data**: Analyze the research notes and extract the following key information:
   - Years of experience: Total professional work experience (as a number)
   - Current company: The company the person currently works at
   - Role: Current job title or position
   - Prior companies: List of previous companies the person has worked at

2. **Assess Information Completeness**: Evaluate whether the extracted information is:
   - Complete and satisfactory for all key fields
   - Missing critical information
   - Contains conflicting or unclear data

3. **Decision Making**: Determine whether additional research is needed based on:
   - How much key information is missing or unclear
   - Whether the current data provides a comprehensive view of the person's professional background
   - If there are gaps that could be filled with more targeted searches

4. **Provide Reasoning**: Explain your decision with specific reasoning about:
   - What information was successfully found
   - What information is missing or unclear
   - Why additional research is or isn't necessary

Please respond in the following JSON format:
{{
    "structured_data": {{
        "years_of_experience": <number or null>,
        "current_company": "<company name or null>",
        "role": "<job title or null>",
        "prior_companies": ["<company1>", "<company2>", ...]
    }},
    "completeness_assessment": "<brief assessment of information quality and completeness>",
    "should_continue_research": <true or false>,
    "reasoning": "<detailed explanation of your decision and what additional information might be needed>"
}}

Focus on extracting factual information from the research notes. If information is not clearly stated or is ambiguous, mark it as null rather than making assumptions."""


