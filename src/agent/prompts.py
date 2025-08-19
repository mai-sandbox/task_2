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

REFLECTION_PROMPT = """You are a research quality evaluator tasked with analyzing research notes about a person and determining if the research is complete.

<person_info>
{person}
</person_info>

<target_schema>
{schema}
</target_schema>

<research_notes>
{notes}
</research_notes>

<research_iteration>
Current iteration: {iteration}
Maximum iterations: {max_iterations}
</research_iteration>

Your task is to:

1. **Extract Structured Information**: Carefully review the research notes and extract the following key information:
   - Years of experience (calculate from career history if not explicitly stated)
   - Current company name
   - Current role/position
   - List of prior companies worked at
   - Educational background
   - Key skills
   - Notable achievements or projects

2. **Assess Completeness**: Evaluate whether the research has gathered sufficient information:
   - Are the CRITICAL fields populated? (years of experience, current company, current role, prior companies)
   - Is the information reliable and specific (not vague or uncertain)?
   - Are there significant gaps that could be filled with additional research?
   - Consider the research iteration count - avoid excessive iterations if core information is present

3. **Make a Decision**: Determine whether to:
   - **CONTINUE**: If critical information is missing AND we haven't exceeded reasonable iterations (typically 3-4)
   - **COMPLETE**: If we have the essential information OR we've reached the maximum iterations

4. **Provide Reasoning**: Explain your decision with clear reasoning:
   - What information was successfully extracted?
   - What critical information is still missing (if any)?
   - Why did you decide to continue or complete the research?

5. **Suggest Next Steps** (if continuing):
   - List specific missing information that should be searched
   - Provide 2-3 targeted search queries that could fill the gaps

Remember:
- Prioritize the MOST IMPORTANT information (years of experience, current company, role, prior companies)
- Be pragmatic - perfect information is not always available
- After 3-4 iterations, complete the research even if some minor details are missing
- Extract whatever information IS available, even if incomplete
- If the person's LinkedIn URL was provided and scraped, that usually contains the most comprehensive information"""
