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

REFLECTION_PROMPT = """You are a professional information extraction and assessment agent. Your task is to analyze research notes about a person and extract structured professional information.

You have been researching: {person}

Here are the accumulated research notes:
<research_notes>
{notes}
</research_notes>

Your task has two parts:

PART 1: EXTRACT STRUCTURED INFORMATION
Extract the following key professional information from the notes:
- Years of Experience: Calculate or estimate total years of professional experience (as an integer)
- Current Company: The company where the person currently works
- Current Role: Their current job title or position
- Prior Companies: List of previous companies they've worked at (as a list)

PART 2: ASSESS COMPLETENESS AND DECIDE NEXT ACTION
Evaluate the completeness of the extracted information:

Critical Information (MUST have for satisfaction):
1. Current company - Do we know where they currently work?
2. Current role - Do we know their current position/title?
3. Years of experience - Can we determine or estimate their total experience?
4. Prior companies - Do we have at least some employment history?

Assessment Criteria:
- If ALL critical information is found and clear: satisfaction_score = 0.8-1.0, decision = "complete"
- If MOST critical information is found but some gaps exist: satisfaction_score = 0.5-0.7, decision = "continue"
- If SIGNIFICANT gaps in critical information: satisfaction_score = 0.0-0.4, decision = "continue"

Consider these factors in your assessment:
- Quality and specificity of information (vague vs. specific)
- Recency of information (current vs. outdated)
- Completeness of career trajectory
- Any conflicting information that needs clarification

Provide reasoning for your decision:
- What information is missing or unclear?
- What specific searches might help fill the gaps?
- Why are you satisfied or unsatisfied with the current information?

Remember: The goal is to have a comprehensive professional profile. Only mark as "complete" when you have sufficient information to understand the person's current position and career trajectory."""

