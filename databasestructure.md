company
- company_id (PK)
- name
- industry
- country

department
- dept_id (PK)
- company_id (FK -> company.company_id)
- name

employee
- employee_id (PK)
- company_id (FK -> company.company_id)
- dept_id (FK -> department.dept_id)
- name
- role
- hire_date
- exit_date (nullable)

source_document
- source_id (PK)
- doc_type
- title
- published_date
- file_path
- notes

hr_record
- hr_id (PK)
- company_id (FK -> company.company_id)
- employee_id (FK -> employee.employee_id)
- period
- attendance_days
- performance_summary
- warning_count
- ai_justification
- source_id (FK -> source_document.source_id)

sales_record
- sales_id (PK)
- company_id (FK -> company.company_id)
- employee_id (FK -> employee.employee_id, nullable)
- dept_id (FK -> department.dept_id)
- period
- product
- amount
- region
- ai_justification
- source_id (FK -> source_document.source_id)

finance_record
- finance_id (PK)
- company_id (FK -> company.company_id)
- dept_id (FK -> department.dept_id, nullable)
- period
- metric_name
- amount
- unit
- ai_justification
- source_id (FK -> source_document.source_id)

marketing_record
- marketing_id (PK)
- company_id (FK -> company.company_id)
- period
- campaign_name
- metric_name
- amount
- ai_justification
- source_id (FK -> source_document.source_id)

supply_record
- supply_id (PK)
- company_id (FK -> company.company_id)
- period
- product
- inventory_level
- demand_forecast
- shortage_flag
- ai_justification
- source_id (FK -> source_document.source_id)

legal_record
- legal_id (PK)
- company_id (FK -> company.company_id)
- policy_name
- rule_text
- ai_justification
- source_id (FK -> source_document.source_id)

decision_case
- case_id (PK)
- company_id (FK -> company.company_id)
- question
- target_type
- target_id
- created_at
- status

case_evidence
- evidence_id (PK)
- case_id (FK -> decision_case.case_id)
- source_table
- record_id
- relevance_score
- notes

decision_output
- decision_id (PK)
- case_id (FK -> decision_case.case_id)
- recommendation
- risk_level
- rationale
- ai_justification
- created_at