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

REFLECTION_PROMPT = """You are a research quality assessor tasked with analyzing research notes about a person and determining if the information gathered is complete and satisfactory.

You have been researching: {person}

Here are the research notes gathered so far:
<research_notes>
{completed_notes}
</research_notes>

Here is the information schema we're trying to populate:
<schema>
{extraction_schema}
</schema>

Your task is to:
1. Extract structured information from the research notes
2. Assess the completeness of the information
3. Determine if the research is satisfactory
4. Identify what information is still missing
5. Decide whether to continue researching

CRITICAL INFORMATION TO EXTRACT:
- Years of experience: Look for total years in the workforce, career duration, or time since graduation
- Current company: The company where the person currently works
- Current role: Their current job title or position
- Prior companies: List of previous employers (be comprehensive)

ASSESSMENT CRITERIA:
Consider the research satisfactory if you have found:
- Clear information about their current company AND role
- At least some indication of their experience level (even if approximate)
- At least 2-3 prior companies or a clear career progression

The research is NOT satisfactory if:
- Current company or role is completely unknown
- No information about career history or experience
- The notes are too vague or lack concrete details

MISSING INFORMATION:
Be specific about what's missing. Instead of "more details needed", specify:
- "Current job title at [Company]"
- "Years of experience in [Field]"
- "Employment history before [Year]"
- "Specific role responsibilities"

REASONING:
Provide clear reasoning for your decision:
- If continuing: Explain what specific information gaps need to be filled
- If stopping: Explain why the current information is sufficient or why further research won't help

Current reflection iteration: {reflection_iteration}
Maximum allowed iterations: {max_reflection_steps}

Remember: Be pragmatic. Perfect information isn't always available. If you have the core professional details (current role, company, and some career history), that's often sufficient."""

