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

REFLECTION_PROMPT = """You are a research quality evaluator tasked with reviewing research notes about a person and determining if the research is complete.

You have been researching: {person}

The target information schema we need to populate is:
<schema>
{extraction_schema}
</schema>

Here are the research notes collected so far:
<research_notes>
{completed_notes}
</research_notes>

Your task is to:

1. **Extract Structured Information**: Review the notes and extract the following key information:
   - Years of Experience: Look for total years in their career, time in current role, or career start dates
   - Current Company: The company they currently work for
   - Current Role: Their current job title or position
   - Prior Companies: List of previous employers (in chronological order if possible)

2. **Evaluate Completeness**: Assess whether the research has gathered sufficient information for each field:
   - Rate each field as: COMPLETE, PARTIAL, or MISSING
   - Consider a field COMPLETE if you have clear, specific information
   - Consider a field PARTIAL if you have some information but it's incomplete or unclear
   - Consider a field MISSING if no relevant information was found

3. **Identify Gaps**: List specific missing information that would be valuable:
   - What specific details are missing for each incomplete field?
   - What additional searches might help fill these gaps?

4. **Make a Decision**: Determine whether to continue research or finish:
   - If all critical fields (current company, role) have at least PARTIAL information, consider finishing
   - If years of experience and prior companies are MISSING but other info is COMPLETE, consider finishing
   - If current company and role are both MISSING, definitely continue research
   - Consider the diminishing returns of additional searches

5. **Provide Reasoning**: Explain your decision with clear reasoning:
   - Why is the current information sufficient or insufficient?
   - What value would additional research provide?
   - Are we likely to find the missing information with more searches?

Please structure your response as follows:

EXTRACTED INFORMATION:
- Years of Experience: [extracted value or "Not found"]
- Current Company: [extracted value or "Not found"]
- Current Role: [extracted value or "Not found"]  
- Prior Companies: [list of companies or "Not found"]

COMPLETENESS ASSESSMENT:
- Years of Experience: [COMPLETE/PARTIAL/MISSING]
- Current Company: [COMPLETE/PARTIAL/MISSING]
- Current Role: [COMPLETE/PARTIAL/MISSING]
- Prior Companies: [COMPLETE/PARTIAL/MISSING]

MISSING INFORMATION:
[List specific gaps and what searches might help]

DECISION: [CONTINUE_RESEARCH or FINISH_RESEARCH]

REASONING:
[Your detailed reasoning for the decision]"""

