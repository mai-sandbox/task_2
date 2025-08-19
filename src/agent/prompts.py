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

REFLECTION_PROMPT = """You are a research analyst tasked with reflecting on research notes about a person and converting them to structured format.

Here are the research notes collected:
<notes>
{notes}
</notes>

Please analyze these notes and extract structured information focusing on:
- Years of experience (total professional experience)
- Current company
- Current role/title 
- Prior companies worked at (chronological order if possible)
- Any other relevant professional information

After structuring the information, determine:
1. Is the current information satisfactory for a comprehensive profile?
2. What key information is missing that would be valuable?
3. Should we conduct additional research or is this sufficient?

Provide your analysis in the following JSON format:
{{
  "structured_info": {{
    "years_of_experience": "number or range if available",
    "current_company": "company name or null",
    "current_role": "job title or null", 
    "prior_companies": ["list of previous companies"],
    "other_info": {{}}
  }},
  "analysis": {{
    "is_satisfactory": true/false,
    "missing_information": ["list of missing key information"],
    "continue_research": true/false,
    "reasoning": "detailed reasoning for the decision"
  }}
}}

Be thorough in your analysis and provide specific reasoning for whether to continue research."""
