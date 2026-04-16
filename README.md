# DREAM-KG-Exploration
By using LLMs to querry and identify missing data.

Overview:
This repository demonstrates a methodology for using Large Language Models (LLMs) to autonomously query and identify missing data in a Knowledge Graph (Dream KG).

This approach uses an Agentic Loop where the AI:

Generates the Query: Translates a natural language goal into a specific KG query.

Analyzes the Structure: Audits the returned data to find logical "holes" or missing relationships.

Identifies Gaps: Points out exactly what data is needed to complete the graph's knowledge.

How it Works:

Query Generation: Using Claude to write complex KG queries based on high-level goals.

Data Export: Processing graph data as CSV for structured AI analysis.

Autonomous Gap Detection: Prompting the AI to find missing links within the dataset.
