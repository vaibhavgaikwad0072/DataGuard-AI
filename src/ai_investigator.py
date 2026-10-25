
import json
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


load_dotenv()


# -----------------------------------------------
# 1. Define the expected AI output structure
# -----------------------------------------------

class InvestigationFinding(BaseModel):
    title: str = Field(
        description="Short title describing the finding."
    )

    severity: Literal[
        "low", "medium", "high", "critical"
    ] = Field(
        description="Severity based on the supplied evidence."
    )

    evidence: list[str] = Field(
        description="Specific facts taken from the supplied reports."
    )

    explanation: str = Field(
        description="Explain what changed without inventing causes."
    )

    recommended_actions: list[str] = Field(
        description="Practical actions for a data engineer."
    )


class InvestigationReport(BaseModel):
    summary: str = Field(
        description="Brief summary of the overall findings."
    )

    findings: list[InvestigationFinding]

    limitations: list[str] = Field(
        description="Important uncertainties or missing information."
    )


# -----------------------------------------------
# 2. Configure the language model
# -----------------------------------------------

def create_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        api_key=api_key,
    )


# -----------------------------------------------
# 3. Create the investigation prompt
# -----------------------------------------------



INVESTIGATION_PROMPT = PromptTemplate.from_template("""
You are DataGuard AI, an intelligent data reliability investigator.

Analyze the current data quality report and historical drift results.
Use previous investigations as additional context when available.

CURRENT QUALITY REPORT:
{quality_report}

CURRENT DRIFT RESULTS:
{drift_results}

PREVIOUS INVESTIGATIONS:
{historical_context}

RULES:
1. Base current findings on the current quality report and drift results.
2. Use historical investigations only to identify recurring issues and changes over time.
3. Never treat a historical metric as a current metric.
4. Never invent metrics, counts, percentages, or findings.
5. Distinguish observed facts from possible explanations.
6. Do not claim causation without supporting evidence.
7. Negative quantities may represent legitimate returns or credit transactions.
8. Missing CustomerID values should be investigated, not automatically deleted.
9. Recommend practical and safe actions.
10. Mention limitations when evidence is insufficient.
11. Return no more than 5 findings.
12. Severity must be one of: low, medium, high, critical.
13. Return valid JSON only, as one JSON object.
14. If historical context is empty, analyze the current data normally.
15. Do not claim an issue is recurring unless previous reports support that conclusion.
21. Treat programmatically detected recurrence as evidence that a finding appeared in multiple investigation reports.
22. Do not interpret recurrence alone as proof that the underlying data quality has deteriorated.
23. Use the supplied occurrence count and investigation IDs accurately.
24. Do not claim that an issue is recurring if the recurrence detector did not identify it.


Return a single valid JSON object with exactly this structure:

{{
  "summary": "A concise summary of the investigation.",
  "findings": [
    {{
      "title": "Missing CustomerID",
      "severity": "medium",
      "evidence": [
        "Evidence directly supported by the input"
      ],
      "explanation": "Explain the finding using the available evidence.",
      "recommended_actions": [
        "Investigate the source of missing values."
      ]
    }}
  ],
  "limitations": [
    "Describe limitations of the available evidence."
  ]
}}

Mandatory requirements:
- Always include summary, findings, and limitations.
- All three top-level fields are required.
- summary must be a string.
- findings must be a list of finding objects.
- Each finding must contain title, severity, evidence, explanation, and recommended_actions.
- limitations must be a list of strings.
- If there are no limitations to report, use an empty list.
- Do not omit any required field.
- Return valid JSON only.
- Do not include Markdown fences or text outside the JSON object.


""")





# -----------------------------------------------
# 4. Run the AI investigation
# -----------------------------------------------

def investigate_data(
    quality_report: dict,
    drift_results: list[dict],
    historical_context: list[dict] | None = None,
    recurring_issues: list[dict] | None = None,
) -> InvestigationReport:

    llm = create_llm()

    json_llm = llm.bind( response_format={"type": "json_object"} )

    chain = INVESTIGATION_PROMPT | json_llm

    response = chain.invoke({
        "quality_report": json.dumps(
            quality_report,
            indent=2,
            default=str,
        ),
        "drift_results": json.dumps(
            drift_results,
            indent=2,
            default=str,
        ),
        "historical_context": json.dumps(
        historical_context or [],
        indent=2,
        default=str),
        "recurring_issues": json.dumps(
        recurring_issues or [],
        indent=2,
        default=str,
    ),
    })
    content = response.content
    if isinstance(content, list): 
        content = "".join( item.get("text", "") 
                          for item in content 
                          if isinstance(item, dict) )
    if not isinstance(content, str) or not content.strip(): 
        raise ValueError( "The AI returned an empty investigation report." )
    
   
    try:
        result = InvestigationReport.model_validate_json(content)

    except Exception as exc:
        print("\nAI response that failed validation:")
        print(content)

        raise ValueError(
            "The AI response did not match InvestigationReport. "
            "Inspect the printed response for missing or invalid fields."
        ) from exc




    return result

