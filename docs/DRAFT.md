## The Recommended 4-Mode CLI Structure

The main command could be something like `ra-assist` or `research-cli`.

### Mode 1: `lit` (Literature & Knowledge Agent)

This agent is configured for external tool use (like Google Search, ArXiv API, PDF ingestion) and rapid
information synthesis. It's focused on **answering the "what is" and "what do others say" questions.**

| CLI Mode            | Sub-Command     | Description                                                                          | Example Usage                                                               |
| :------------------ | :-------------- | :----------------------------------------------------------------------------------- | :-------------------------------------------------------------------------- |
| **`ra-assist lit`** | **`search`**    | Comprehensive search across academic and web sources.                                | `ra-assist lit search "Impact of climate change on coastal infrastructure"` |
|                     | **`summarize`** | Ingest a file (PDF/URL) and return a concise summary and critique.                   | `ra-assist lit summarize ./paper.pdf`                                       |
|                     | **`compare`**   | Analyze a directory of files and generate a comparison table on key metrics.         | `ra-assist lit compare ./papers/ --criteria "methodology, results"`         |
|                     | **`trend`**     | Analyze a set of abstracts/papers to identify emerging research gaps or key authors. | `ra-assist lit trend ./directory/2020_to_2024`                              |

### Mode 2: `data` (Data Analysis & Code Agent)

This agent is configured with **code execution tools** (Python/R interpreters) and is focused on **answering
the "what is the relationship" and "how do I calculate" questions.**

| CLI Mode             | Sub-Command   | Description                                                               | Example Usage                                                                      |
| :------------------- | :------------ | :------------------------------------------------------------------------ | :--------------------------------------------------------------------------------- |
| **`ra-assist data`** | **`clean`**   | Analyze a raw CSV/Excel file, suggest and execute a cleaning script.      | `ra-assist data clean raw_data.csv --strategy "outliers=drop"`                     |
|                      | **`analyze`** | Run a specific statistical test or regression model based on a prompt.    | `ra-assist data analyze cleaned.csv --test "t-test" --groups "male, female"`       |
|                      | **`script`**  | Generate and explain a specific analysis script for later human review.   | `ra-assist data script "Generate an R script for a 3-way ANOVA"`                   |
|                      | **`viz`**     | Generate a publication-quality chart or graph based on a file and prompt. | `ra-assist data viz results.csv --type "scatterplot" --x "Income" --y "Happiness"` |

### Mode 3: `write` (Drafting & Documentation Agent)

This agent is configured with a focus on **text generation, adherence to style guides, and structural
formatting**. It's focused on **answering the "how should this be written" questions.**

| CLI Mode              | Sub-Command    | Description                                                            | Example Usage                                                              |
| :-------------------- | :------------- | :--------------------------------------------------------------------- | :------------------------------------------------------------------------- |
| **`ra-assist write`** | **`draft`**    | Generate the first draft of a specific section or document type.       | `ra-assist write draft --type "abstract" --topic "LLM agent productivity"` |
|                       | **`refine`**   | Ingest a text and critique/edit it for clarity, grammar, and tone.     | `ra-assist write refine protocol.txt --tone "professional, objective"`     |
|                       | **`cite`**     | Convert a raw bibliography list or text into a specific style.         | `ra-assist write cite paper.txt --style "APA 7th"`                         |
|                       | **`irb-prep`** | Assist in drafting specific compliance forms (e.g., Informed Consent). | `ra-assist write irb-prep consent.txt --study "Survey of remote workers"`  |

### Mode 4: `query` (Global/Utility Agent)

This is your general, quick-help mode. It's a highly flexible agent for miscellaneous, less structured, or
quick-turnaround tasks that don't fit into the other specific categories.

| CLI Mode              | Sub-Command  | Description                                                                                                             | Example Usage                                                           |
| :-------------------- | :----------- | :---------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------- |
| **`ra-assist query`** | **`ask`**    | A general, powerful Q&A tool for quick, complex reasoning (like a standard GPT interface, but in your specialized CLI). | `ra-assist query "What are the common pitfalls of mediation analysis?"` |
|                       | **`tool`**   | Quick conversion, translation, or simple scripting.                                                                     | `ra-assist query tool "Convert 50 meters to feet"`                      |
|                       | **`config`** | Manage API keys, default directories, and agent settings.                                                               | `ra-assist query config set_style "APA"`                                |

By adopting this structure, you switch from interacting with a single, often confused generalist to
specialized, tool-equipped experts, which drastically increases the reliability and quality of the agent's
output.
