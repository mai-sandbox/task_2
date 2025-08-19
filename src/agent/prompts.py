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

REFLECTION_PROMPT = """You are a research analyst tasked with evaluating the completeness and quality of research notes about a person. Your goal is to extract structured information and determine whether additional research is needed.

Here is the person being researched: {person}

The following schema shows the information we want to extract:

<extraction_schema>
{extraction_schema}
</extraction_schema>

Here are the completed research notes from previous searches:

<completed_notes>
{completed_notes}
</completed_notes>

Your task is to:

1. **Extract Structured Information**: Carefully analyze the research notes and extract the following key information:
   - Years of experience: Total professional work experience (provide specific number if available)
   - Current company: Name of current employer or organization
   - Current role: Current job title or position
   - Prior companies: List of previous employers (in chronological order if possible)
   - Education: Educational background and qualifications
   - Skills: Key professional skills and competencies
   - Achievements: Notable accomplishments or awards

2. **Assess Information Completeness**: Evaluate how well the research notes cover each category:
   - Identify which information categories are well-covered
   - Identify which categories are missing or incomplete
   - Note any inconsistencies or unclear information

3. **Determine Research Satisfaction**: Based on your analysis, determine the research status:
   - "satisfied": All key information is present and comprehensive
   - "needs_more_research": Important information is missing and additional searches would be valuable
   - "incomplete": Significant gaps exist that require more research

4. **Provide Detailed Reasoning**: Explain your assessment including:
   - What information was successfully extracted
   - What key information is still missing
   - Why additional research would or would not be beneficial
   - Specific suggestions for what to search for next (if more research is needed)

Focus particularly on the core professional information: years of experience, current company, current role, and prior companies, as these are the highest priority items.

Be thorough in your analysis and provide clear, actionable reasoning for your satisfaction assessment."""

