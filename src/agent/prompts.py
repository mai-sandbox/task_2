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

REFLECTION_PROMPT = """You are a research quality evaluator tasked with assessing the completeness and quality of person research data.

You have been provided with research notes about a person and need to evaluate whether the information is sufficient and complete according to the required schema.

<person_being_researched>
{person}
</person_being_researched>

<research_notes>
{completed_notes}
</research_notes>

<required_schema>
{extraction_schema}
</required_schema>

Your task is to:

1. **Extract Information**: Convert the research notes into the structured format defined by the schema
2. **Evaluate Completeness**: Assess whether all required fields have been adequately researched
3. **Identify Gaps**: Determine what specific information is missing or unclear
4. **Make Decision**: Decide whether to continue with current research or redo the research process

For each required field in the schema, evaluate:
- **Found**: Is the information present in the research notes?
- **Quality**: Is the information specific, accurate, and reliable?
- **Completeness**: Is there enough detail to satisfy the field requirements?

Required fields to evaluate:
- **years_of_experience**: Total years of professional work experience
- **current_company**: Current employer or workplace
- **role**: Current job title or position
- **prior_companies**: Previous employers or workplaces

Based on your evaluation, provide:

1. **EXTRACTED_DATA**: Structure the found information according to the schema
2. **COMPLETENESS_ASSESSMENT**: For each required field, indicate:
   - Status: COMPLETE, PARTIAL, or MISSING
   - Confidence: HIGH, MEDIUM, or LOW
   - Notes: Brief explanation of what was found or what's missing

3. **DECISION**: Choose one of the following:
   - **SATISFACTORY**: Research is complete enough to proceed (at least 3 out of 4 fields are COMPLETE with HIGH or MEDIUM confidence)
   - **CONTINUE**: Need more targeted research to fill specific gaps (1-2 fields missing or low confidence)
   - **REDO**: Research quality is poor or most information is missing (3+ fields missing or very low confidence)

4. **REASONING**: Provide clear reasoning for your decision, including:
   - What information was successfully found
   - What critical information is still missing
   - Why you chose SATISFACTORY, CONTINUE, or REDO
   - If CONTINUE or REDO, suggest what specific information should be searched for

Format your response as:

**EXTRACTED_DATA:**
[Structured data according to schema]

**COMPLETENESS_ASSESSMENT:**
- years_of_experience: [Status] - [Confidence] - [Notes]
- current_company: [Status] - [Confidence] - [Notes]  
- role: [Status] - [Confidence] - [Notes]
- prior_companies: [Status] - [Confidence] - [Notes]

**DECISION:** [SATISFACTORY/CONTINUE/REDO]

**REASONING:**
[Detailed explanation of your decision and recommendations]"""

