Use the interview-prep agent to prepare comprehensive interview preparation materials for the following role:

$ARGUMENTS

If $ARGUMENTS is a posting folder name (e.g. google-customer-engineer-outcome-saas), read it from postings/[slug]/. If it's a URL, fetch it. If no arguments are provided, check postings/tracker.yaml for the most recent application in "interviewing" status and use that.

Run the full preparation pipeline: process_research → company_research → compensation_research → round_prep (for each round) → story_bank. Save all files to output/interview_prep/[company]_[role]_[YYYY-MM-DD]/.
