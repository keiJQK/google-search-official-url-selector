# google-search-official-url-selector
Generate Google Search queries, normalize results to CSV, and select likely official-site URLs via rule-based scoring.

# Google Search Pipeline
A preprocessing pipeline that generates Google search queries,
normalizes search results into CSV format,
and evaluates which URL is most likely the official website
using a transparent, rule-based scoring system.
The output is designed for downstream scraping workflows.

## How to Run
- This repository assumes an external scraping implementation
  (e.g. a Selenium or Requests-based runner) is available.
- The Google Search pipeline itself is executed from
  `pipeline_google_search.py`, which serves as the single entry point.
- Relative imports are assumed; run the script from the repository root
  without relying on PYTHONPATH.
- See: [HOW_TO_RUN.md](./HOW_TO_RUN.md)

Example:
python -m pipeline_google_search

## Why this exists
- **Problem:** When scraping Google search results, it is difficult to
  automatically determine which URL corresponds to the official website,
  resulting in wasted scraping effort on irrelevant or noisy pages.
- **Goal:** Introduce a deterministic preprocessing step that converts
  search queries into structured data and selects official-site candidates
  before downstream scraping.
- **Output:** A CSV file of evaluated search results where the most likely
  official site is marked with `is_access=True`.

## Constraints / Trade-offs
- **Rule-based evaluation only:** No machine learning is used.
  The scoring logic is intentionally simple and explainable.
- **Sensitive to search result changes:** Changes in Google search behavior
  or result structure may reduce accuracy.
- **Accuracy vs explainability:** The design favors reproducibility and
  reasoning transparency over maximum recall.

## Next improvements (planned)
- Externalize scoring weights and keyword rules into configuration files.
- Move exclusion domain lists out of code.
- Improve query generation logic for better coverage and precision.

## Intended Use Cases
- Identify official websites from company or service names.
- Preprocessing stage for Selenium / Requests-based scraping pipelines.
- Noise reduction when running large batches of Google searches.

## Architecture / Directory Structure
This repository adopts a layered structure to keep responsibilities clear
and replaceable.

- pipeline_google_search.py  
  Entry point of the pipeline and overall execution control.

- runner (google_search_runner.py)  
  Orchestration layer that wires usecases together.
  No evaluation logic or I/O implementation.

- usecase (google_search_usecase.py)  
  Workflow steps such as query generation, dataset preparation,
  and official-site evaluation logic.

- infrastructure (google_search_infrastructure.py)  
  External concerns such as CSV I/O, path resolution, and URL construction.

The project is workflow-driven.
Shared objects mainly act as pipeline context / DTOs
rather than stable domain models.

### Processing Flow
Initialization
- Pipeline context (GoogleSearchContext) is created.
- Infrastructure classes provide file and data access utilities.

Execution Flow
- Runner
  -> PrepUserInput (prepare search keywords; currently debug data)
  -> PrepSearchUsecase (generate Google search URLs and save CSV)
  -> Scraping (external process; not included in this repository)
  -> Evaluation (score and select official website candidates)

## Data Outputs
CSV outputs
- output-google-search-level-1_1.csv  
  Generated search queries and corresponding URLs.

- output-google-search-level-2_1.csv  
  Scraping results produced by an external scraping step.

- evaluation-google-search.csv  
  Evaluation results with official-site flags.

## Current Limitations
- **Debug-only user input**  
  Search keywords are currently hardcoded for debugging purposes.
- **Fragile against search behavior changes**  
  The pipeline assumes stable Google search behavior and may require
  adjustments if results change.
- **No multilingual or regional support**  
  Evaluation logic does not yet adapt to language or country-specific rules.
