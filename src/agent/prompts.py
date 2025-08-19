"""Prompt templates for the people researcher agent."""

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

REFLECTION_PROMPT = """You are a research quality assessor. Your task is to analyze research notes about a person and convert them into a structured format, then assess whether the information is satisfactory.

Here is the person being researched: {person}

Here are the research notes collected so far:
<notes>
{notes}
</notes>

Required information schema:
<schema>
{schema}
</schema>

Your task is to:
1. Extract and structure all available information according to the schema
2. Assess the quality and completeness of the information
3. Identify what key information is missing
4. Determine if additional research is needed

Please provide your response in the following JSON format:
{{
    "structured_data": {{
        "years_of_experience": "extracted value or null",
        "current_company": "extracted value or null", 
        "current_role": "extracted value or null",
        "prior_companies": "list of companies with roles and durations or null",
        "education": "educational background or null",
        "skills": "key skills or null",
        "achievements": "notable accomplishments or null"
    }},
    "assessment": {{
        "completeness_score": 0.0-1.0,
        "confidence_score": 0.0-1.0,
        "missing_critical_info": ["list of missing critical information"],
        "missing_optional_info": ["list of missing optional information"],
        "data_quality": "assessment of information reliability"
    }},
    "recommendations": {{
        "needs_more_research": true/false,
        "suggested_search_queries": ["additional queries to run if more research needed"],
        "reasoning": "explanation for recommendation"
    }}
}}

Focus especially on: years of experience, current company, role, and prior companies as these are the most important."""
