\# AI Prompt History



\## Purpose



I used Claude as an AI assistant while developing, testing, and reviewing my Workforce Planning System. I used it to understand the challenge requirements, troubleshoot errors, review business logic, improve tests, interpret terminal output, and organize the project documentation. I reviewed the suggested changes and ran the relevant checks to verify the reported results.



\## Tools Used



\- \*\*Python:\*\* To run the application code and validation scripts.

\- \*\*Pandas and NumPy:\*\* To process workforce data and perform calculations.

\- \*\*Streamlit:\*\* To build the interactive dashboard.

\- \*\*pytest:\*\* To execute automated tests.

\- \*\*Git and GitHub:\*\* To track code changes and publish the project repository.

\- \*\*PowerShell:\*\* To execute commands in the local Windows environment.

\- \*\*Claude:\*\* To assist with understanding the challenge, debugging, reviewing business logic, preparing tests and documentation, and interpreting errors and test results.



\## How I Used AI During the Project



| Task | How Claude Helped | What I Verified |

|---|---|---|

| Reviewing workforce capacity logic | I requested assistance in reviewing the skill-gap analysis and capacity reservation logic, particularly the risk of allocating the same employee's available capacity more than once. | I reviewed the changes in `src/business\_logic.py` and ran tests and verification scripts. |

| Testing and validation | I requested help designing checks to ensure that reservations remained within each employee's remaining capacity and that reserved employees met the eligibility requirements. | The recorded test run, `python -m pytest -v`, reported 12 passing tests. The recorded full-data checks reported zero capacity violations and zero ineligible reservation pairs. |

| Protecting existing data | I requested a safer approach for running full-data validation without overwriting the original processed output. | The verification scripts used temporary copies of the CSV data. A recorded hash comparison confirmed that `data/processed/GapAnalysis.csv` matched its baseline after verification. |

| Debugging and command-line operations | I requested step-by-step assistance with interpreting PowerShell commands, resolving Git workflow issues, and pushing the project to GitHub. | The recorded push to the `main` branch succeeded. I checked the Git status and ensured that temporary and backup files were excluded from the commit. |



\## What AI Helped Me Accomplish More Efficiently



Claude helped me break a complex task into smaller, manageable steps, reason through shared-capacity allocation rules, develop focused tests and validation scripts, interpret terminal output, and organize project documentation. This assistance was particularly useful when I was uncertain about the next steps in the development process.



\## Areas Where I Relied on AI Most



I relied primarily on Claude for troubleshooting, reviewing selected parts of the business logic, structuring tests and verification scripts, and understanding the Git workflow. I did not treat AI-generated suggestions alone as proof of correctness. Instead, I used test runs and verification results to check specific aspects of the system's behavior.



\## What I Personally Checked



During the recorded development and verification process, I:



\- Reviewed the changes made to `src/business\_logic.py`.

\- Ran `python -m pytest -v`, which reported 12 passing tests.

\- Successfully ran `python -m py\_compile src/business\_logic.py`.

\- Executed full-data capacity and eligibility checks using temporary copies of the data.

\- Verified that the original processed file, `data/processed/GapAnalysis.csv`, remained unchanged after validation.

\- Checked the Git status and confirmed that the changes were pushed to the GitHub `main` branch.



\## Conclusion



AI assistance supported my development and verification workflow by helping me understand requirements, troubleshoot issues, and improve the organization of my code and tests. I reviewed the suggested changes and used the recorded test and validation results to assess the specific behaviors checked during the project. This process helped me develop a better understanding of workforce planning logic, software testing, data validation, and version control.

