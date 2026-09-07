# Fit and keyword mapping

Use a requirement-to-evidence table rather than a keyword leaderboard. Decompose the JD into central responsibilities, stated qualifications, environment, tools, and outcomes. Preserve alternatives and required/preferred distinctions from the requirement-triage reference.

| Requirement or concept | Resume source | Evidence status | Action and placement |
|---|---|---|---|
| IAM control design | Skills lists IAM only | Claimed only | Keep IAM in relevant skills; ask for a real design example before adding a design bullet |
| Leadership reporting | “Created dashboards and reports for leadership” | Demonstrated deliverable; result unknown | Move relevant bullet earlier; ask what reporting informed |
| Azure AD / Entra ID | Azure AD stated | Same directory product under renamed branding | Use “Microsoft Entra ID (formerly Azure AD)” if this describes the candidate's actual work |
| Splunk required | Sentinel detections documented | Adjacent product experience | Explain detection method with Sentinel; do not list Splunk as used |

## Language rules

Use natural JD wording where it describes the same work. Expand an acronym when it helps this audience or bridges wording in the JD; do not expand every acronym mechanically. Keep ambiguous terms explicit: SOC can refer to an operations center or SOC reporting, VM to virtual machines or vulnerability management, and IR to different fields.

A tool listed in skills is a candidate claim. It does not require a separate bullet for every basic technology. Prioritize evidence for the few capabilities central to the job. Presence elsewhere is not proof of use; “studying Terraform” and “no Terraform experience” are not production experience.

Keep summary, skills, and experience complementary. A concise truthful tool list can help discovery; repetition and hidden keywords do not establish qualification. Never add a term merely because it appears in analyzer output.

## Common domain language to consider

Select from the candidate's evidence, not this list as a target checklist:

- IT operations: service desk, incident and change management, DNS/DHCP, directory services, endpoint management, backups, restore testing, troubleshooting, automation.
- Infrastructure/platform: Linux/Windows, networking, cloud, IaC, CI/CD, Kubernetes, observability, availability, recovery, capacity and cost management.
- Detection/response: telemetry, investigation, triage, SIEM/EDR, detection validation, containment, recovery, KQL/SPL/Sigma/YARA when actually used.
- Exposure/identity: asset ownership, exploitability, EPSS, KEV, CVSS, remediation, exceptions, IAM/PAM/IGA, MFA/SSO, lifecycle and access review.
- AppSec/product: threat modeling, secure SDLC, code review, API security, SAST/DAST/SCA, developer remediation, verification.
- Risk/leadership: control design/testing, audit evidence, risk decisions, roadmaps, budget responsibility, operating model, talent development, governance.

The helper performs lexical matching over a bounded vocabulary. Review unrecognized terms manually. Never report its list as complete JD coverage or use a lexical ratio as role fit.
