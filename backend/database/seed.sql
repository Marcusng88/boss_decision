-- AI Boss Decision Engine - Seed Data (Single Company: TechVenture Solutions)
-- Rich, properly-linked data with realistic IDs and cross-table relationships
-- PostgreSQL / Supabase compatible

-- ============================================
-- DEPARTMENTS (aligned with agent structure)
-- ============================================
INSERT INTO department (dept_id, name, description) VALUES
(101, 'Engineering', 'Software development and DevOps'),
(102, 'Sales', 'Enterprise and SMB sales team'),
(103, 'Marketing', 'Digital marketing and brand'),
(104, 'HR', 'Human resources and talent'),
(105, 'Finance', 'Financial planning and accounting'),
(106, 'Legal', 'Legal compliance and contracts'),
(107, 'Supply Chain', 'Procurement and vendor management');

-- ============================================
-- EMPLOYEES (40+ employees across departments)
-- ============================================

-- Engineering (dept 101) - 12 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1001, 101, 'Ahmad Hassan', 'Senior Backend Engineer', 'ahmad.hassan@techventure.my', '2022-03-15', 12500.00),
(1002, 101, 'Li Wei', 'Frontend Developer', 'li.wei@techventure.my', '2023-01-10', 9800.00),
(1003, 101, 'Priya Kumar', 'DevOps Lead', 'priya.kumar@techventure.my', '2021-06-01', 14200.00),
(1004, 101, 'Tan Jia Hui', 'Full Stack Developer', 'jia.hui@techventure.my', '2023-08-20', 10500.00),
(1005, 101, 'Omar Sharif', 'Backend Engineer', 'omar.sharif@techventure.my', '2022-11-12', 11000.00),
(1006, 101, 'Chen Yi', 'QA Engineer', 'chen.yi@techventure.my', '2023-02-14', 8500.00),
(1007, 101, 'Siti Nurhaliza', 'Mobile Developer', 'siti.nur@techventure.my', '2022-09-01', 10800.00),
(1008, 101, 'Rajesh Menon', 'Engineering Manager', 'rajesh.menon@techventure.my', '2020-05-10', 16500.00),
(1009, 101, 'Lina Tan', 'Frontend Developer', 'lina.tan@techventure.my', '2024-01-15', 9200.00),
(1010, 101, 'Hassan Ali', 'Backend Engineer', 'hassan.ali@techventure.my', '2023-06-20', 10200.00),
(1011, 101, 'Kumar Suresh', 'DevOps Engineer', 'kumar.suresh@techventure.my', '2022-07-03', 11800.00),
(1012, 101, 'Fatimah Wong', 'Senior Frontend Engineer', 'fatimah.wong@techventure.my', '2021-10-18', 13500.00);

-- Sales (dept 102) - 10 employees (includes underperformer John Tan #1023)
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1020, 102, 'Sarah Lim', 'Sales Director', 'sarah.lim@techventure.my', '2020-11-05', 18000.00),
(1021, 102, 'David Wong', 'Enterprise Sales Executive', 'david.wong@techventure.my', '2023-02-14', 11500.00),
(1022, 102, 'Alicia Fernandez', 'SMB Sales Executive', 'alicia.f@techventure.my', '2022-04-10', 10200.00),
(1023, 102, 'John Tan', 'Sales Executive', 'john.tan@techventure.my', '2023-08-20', 10500.00), -- UNDERPERFORMER (main case)
(1024, 102, 'Muthu Kumar', 'Enterprise Account Manager', 'muthu.kumar@techventure.my', '2021-07-18', 13800.00),
(1025, 102, 'Nurul Aisyah', 'Sales Manager', 'nurul.aisyah@techventure.my', '2022-01-12', 15000.00),
(1026, 102, 'Tan Mei Ling', 'SMB Sales Executive', 'mei.ling@techventure.my', '2023-09-05', 9800.00),
(1027, 102, 'Azman Ibrahim', 'Enterprise Sales Executive', 'azman.ib@techventure.my', '2022-06-22', 12200.00),
(1028, 102, 'Rebecca Chong', 'Sales Operations Specialist', 'rebecca.chong@techventure.my', '2023-03-10', 8900.00),
(1029, 102, 'Vincent Lee', 'Sales Development Rep', 'vincent.lee@techventure.my', '2024-02-01', 7500.00);

-- Marketing (dept 103) - 7 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1030, 103, 'Zara Khan', 'Marketing Director', 'zara.khan@techventure.my', '2021-03-08', 16500.00),
(1031, 103, 'Chen Wei', 'Content Marketing Manager', 'chen.wei@techventure.my', '2022-05-12', 11000.00),
(1032, 103, 'Siti Aminah', 'Digital Marketing Specialist', 'siti.aminah@techventure.my', '2023-01-20', 9200.00),
(1033, 103, 'Kumar Singh', 'SEO Specialist', 'kumar.singh@techventure.my', '2022-09-15', 9800.00),
(1034, 103, 'Lisa Tan', 'Graphic Designer', 'lisa.tan@techventure.my', '2023-07-01', 8500.00),
(1035, 103, 'Omar Farid', 'Marketing Analyst', 'omar.farid@techventure.my', '2023-11-10', 8900.00),
(1036, 103, 'Nina Lim', 'Social Media Manager', 'nina.lim@techventure.my', '2024-01-05', 8200.00);

-- HR (dept 104) - 4 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1037, 104, 'Fatimah Zahra', 'HR Director', 'fatimah.zahra@techventure.my', '2020-03-01', 15500.00),
(1038, 104, 'Ahmad Razak', 'HR Manager', 'ahmad.razak@techventure.my', '2021-08-15', 12000.00),
(1039, 104, 'Priya Devi', 'Talent Acquisition Specialist', 'priya.devi@techventure.my', '2022-06-20', 9500.00),
(1040, 104, 'Tan Wei Jie', 'HR Coordinator', 'wei.jie@techventure.my', '2023-10-01', 7800.00);

-- Finance (dept 105) - 5 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1041, 105, 'James Lim', 'CFO', 'james.lim@techventure.my', '2019-09-15', 22000.00),
(1042, 105, 'Siti Hajar', 'Finance Manager', 'siti.hajar@techventure.my', '2021-04-10', 13500.00),
(1043, 105, 'Kumar Raj', 'Senior Accountant', 'kumar.raj@techventure.my', '2022-02-18', 10500.00),
(1044, 105, 'Lina Chen', 'Financial Analyst', 'lina.chen@techventure.my', '2023-05-22', 9200.00),
(1045, 105, 'Hassan Osman', 'Accounts Payable Specialist', 'hassan.osman@techventure.my', '2023-09-12', 7500.00);

-- Legal (dept 106) - 2 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1046, 106, 'David Tan', 'General Counsel', 'david.tan@techventure.my', '2020-07-01', 18500.00),
(1047, 106, 'Aisha Noor', 'Legal Associate', 'aisha.noor@techventure.my', '2022-11-15', 10800.00);

-- Supply Chain (dept 107) - 3 employees
INSERT INTO employee (employee_id, dept_id, name, role, email, hire_date, salary) VALUES
(1048, 107, 'Azman Yusof', 'Procurement Manager', 'azman.yusof@techventure.my', '2021-05-20', 12500.00),
(1049, 107, 'Nina Wong', 'Vendor Relations Specialist', 'nina.wong@techventure.my', '2022-08-10', 9000.00),
(1050, 107, 'Kumar Ariff', 'Supply Chain Analyst', 'kumar.ariff@techventure.my', '2023-12-01', 8800.00);

-- ============================================
-- SOURCE DOCUMENTS (~25 documents)
-- ============================================
INSERT INTO source_document (source_id, doc_type, title, published_date, file_path, extracted_at) VALUES
(501, 'HR Report', 'Q4 2025 Performance Reviews', '2025-12-20', '/data/uploads/hr_q4_2025.pdf', '2025-12-21 09:30:00'),
(502, 'HR Report', 'Q1 2026 Performance Reviews', '2026-04-01', '/data/uploads/hr_q1_2026.pdf', '2026-04-02 10:15:00'),
(503, 'Sales Log', 'CRM Export Q4 2025', '2025-12-28', '/data/uploads/crm_q4_2025.csv', '2025-12-29 08:00:00'),
(504, 'Sales Log', 'CRM Export Q1 2026', '2026-04-05', '/data/uploads/crm_q1_2026.csv', '2026-04-06 07:45:00'),
(505, 'Finance Report', 'FY2025 Salary Audit', '2026-01-15', '/data/uploads/salary_audit_2025.xlsx', '2026-01-16 14:20:00'),
(506, 'Finance Report', 'Q1 2026 Department Budgets', '2026-04-10', '/data/uploads/budget_q1_2026.xlsx', '2026-04-11 09:00:00'),
(507, 'Legal Policy', 'Employee Termination Policy v3.1', '2025-06-01', '/data/uploads/termination_policy_v3.pdf', '2025-06-02 10:00:00'),
(508, 'Legal Policy', 'Performance Improvement Plan Guidelines', '2025-07-15', '/data/uploads/pip_guidelines.pdf', '2025-07-16 11:30:00'),
(509, 'Marketing Report', 'Q4 2025 Campaign Performance', '2025-12-31', '/data/uploads/marketing_q4_2025.pdf', '2026-01-02 08:30:00'),
(510, 'Marketing Report', 'Q1 2026 Campaign Performance', '2026-04-08', '/data/uploads/marketing_q1_2026.pdf', '2026-04-09 09:15:00'),
(511, 'Supply Chain Log', 'Q4 2025 Procurement Report', '2025-12-30', '/data/uploads/procurement_q4_2025.csv', '2025-12-31 10:00:00'),
(512, 'Supply Chain Log', 'Q1 2026 Inventory Status', '2026-03-31', '/data/uploads/inventory_q1_2026.csv', '2026-04-01 08:00:00'),
(513, 'HR Report', 'Q3 2025 Performance Reviews', '2025-09-30', '/data/uploads/hr_q3_2025.pdf', '2025-10-01 09:00:00'),
(514, 'Sales Log', 'CRM Export Q3 2025', '2025-09-28', '/data/uploads/crm_q3_2025.csv', '2025-09-29 08:15:00'),
(515, 'Finance Report', 'Q3 2025 Financial Summary', '2025-10-10', '/data/uploads/finance_q3_2025.xlsx', '2025-10-11 10:30:00'),
(516, 'Legal Policy', 'Market Expansion Legal Framework', '2025-11-20', '/data/uploads/expansion_legal.pdf', '2025-11-21 09:45:00'),
(517, 'Legal Policy', 'Severance Calculation Guidelines', '2025-06-15', '/data/uploads/severance_calc.pdf', '2025-06-16 10:00:00'),
(518, 'HR Report', 'Employee Warning Letters 2025', '2025-11-30', '/data/uploads/warnings_2025.pdf', '2025-12-01 08:30:00'),
(519, 'Sales Log', 'Lost Deals Analysis Q4 2025', '2026-01-10', '/data/uploads/lost_deals_q4.csv', '2026-01-11 09:00:00'),
(520, 'Marketing Report', 'Q3 2025 Campaign Performance', '2025-10-05', '/data/uploads/marketing_q3_2025.pdf', '2025-10-06 09:30:00'),
(521, 'Supply Chain Log', 'Vendor Performance Q1 2026', '2026-04-12', '/data/uploads/vendor_q1_2026.csv', '2026-04-13 08:45:00'),
(522, 'Finance Report', 'Replacement Cost Analysis', '2026-02-20', '/data/uploads/replacement_costs.xlsx', '2026-02-21 10:00:00'),
(523, 'HR Report', 'Exit Interview Summary 2025', '2026-01-20', '/data/uploads/exit_interviews_2025.pdf', '2026-01-21 09:15:00'),
(524, 'Sales Log', 'Pipeline Health Report Q1 2026', '2026-04-15', '/data/uploads/pipeline_q1_2026.csv', '2026-04-16 08:00:00'),
(525, 'Legal Policy', 'Data Privacy Compliance Guidelines', '2025-08-01', '/data/uploads/data_privacy.pdf', '2025-08-02 10:30:00');

-- ============================================
-- HR RECORDS (~42 records - performance reviews for active employees)
-- ============================================

-- John Tan (1023) - UNDERPERFORMER (main case target)
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, absence_days, performance_score, performance_summary, warning_count, pip_status, review_date, reviewer_id, source_id) VALUES
(2001, 1023, '2025-Q3', 62, 3, 2.8, 'Performance below expectations. Missed Q3 sales target by 45%. Limited client engagement.', 0, NULL, '2025-09-25', 1025, 513),
(2002, 1023, '2025-Q4', 58, 7, 2.1, 'Performance declining. Zero deals closed in Q4. Multiple customer complaints received. Attendance issues emerging.', 1, NULL, '2025-12-18', 1025, 501),
(2003, 1023, '2026-Q1', 61, 4, 2.0, 'No improvement observed. Performance review score 2.0/5. Pipeline remains thin. Team morale impact noted. PIP recommended but not yet initiated.', 2, NULL, '2026-03-28', 1020, 502);

-- Sarah Lim (1020) - Sales Director - High performer
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2004, 1020, '2025-Q4', 63, 4.8, 'Exceptional leadership. Team exceeded targets by 22%. Strong strategic vision.', 0, '2025-12-19', 1037, 501),
(2005, 1020, '2026-Q1', 64, 4.9, 'Outstanding quarter. Led enterprise expansion initiative. Promoted to Sales Director.', 0, '2026-03-29', 1037, 502);

-- David Wong (1021) - Strong performer
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2006, 1021, '2025-Q4', 62, 4.2, 'Exceeds expectations. Closed 2 major enterprise deals. Strong pipeline management.', 0, '2025-12-19', 1025, 501),
(2007, 1021, '2026-Q1', 63, 4.3, 'Consistently strong performer. Enterprise segment specialist.', 0, '2026-03-29', 1020, 502);

-- Other sales team members (varied performance)
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2008, 1022, '2026-Q1', 63, 3.8, 'Meets expectations. SMB focus delivering steady results.', 0, '2026-03-29', 1025, 502),
(2009, 1024, '2026-Q1', 64, 4.1, 'Strong account management. High customer retention.', 0, '2026-03-29', 1020, 502),
(2010, 1025, '2026-Q1', 63, 4.5, 'Excellent management skills. Team hitting targets consistently.', 0, '2026-03-29', 1020, 502),
(2011, 1026, '2026-Q1', 62, 3.6, 'Meets expectations. New hire ramping well.', 0, '2026-03-29', 1025, 502),
(2012, 1027, '2026-Q1', 64, 4.0, 'Solid performer. Enterprise deals pipeline healthy.', 0, '2026-03-29', 1020, 502),
(2013, 1028, '2026-Q1', 63, 3.9, 'Reliable ops support. Process improvements implemented.', 0, '2026-03-29', 1020, 502),
(2014, 1029, '2026-Q1', 61, 3.2, 'Acceptable for SDR role. Lead gen targets mostly met.', 0, '2026-03-29', 1025, 502);

-- Engineering team (select members)
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2015, 1001, '2026-Q1', 62, 4.2, 'Strong technical contributions. Delivered 3 major features on time.', 0, '2026-03-30', 1008, 502),
(2016, 1002, '2026-Q1', 63, 3.9, 'Good frontend work. Collaborative team player.', 0, '2026-03-30', 1008, 502),
(2017, 1003, '2026-Q1', 64, 4.8, 'Outstanding DevOps improvements. Reduced deployment time by 40%. Promotion recommended.', 0, '2026-03-30', 1008, 502),
(2018, 1004, '2026-Q1', 61, 3.7, 'Solid contributor. Some mentoring needed on architecture.', 0, '2026-03-30', 1008, 502),
(2019, 1005, '2026-Q1', 63, 4.1, 'Reliable backend engineer. Clean code practices.', 0, '2026-03-30', 1008, 502),
(2020, 1006, '2026-Q1', 62, 3.8, 'Good QA coverage. Automation efforts progressing.', 0, '2026-03-30', 1008, 502),
(2021, 1007, '2026-Q1', 63, 4.0, 'Mobile app progress on track. iOS expertise strong.', 0, '2026-03-30', 1008, 502),
(2022, 1008, '2026-Q1', 64, 4.6, 'Excellent engineering leadership. Team velocity improving.', 0, '2026-03-30', 1037, 502),
(2023, 1009, '2026-Q1', 59, 3.4, 'New hire. Ramping up frontend skills. Needs code review guidance.', 0, '2026-03-30', 1008, 502),
(2024, 1010, '2026-Q1', 63, 3.9, 'Good backend contributions. API design solid.', 0, '2026-03-30', 1008, 502),
(2025, 1011, '2026-Q1', 62, 4.3, 'Strong DevOps support. Infrastructure stability improved.', 0, '2026-03-30', 1008, 502),
(2026, 1012, '2026-Q1', 64, 4.4, 'Senior frontend leadership. Mentoring junior developers effectively.', 0, '2026-03-30', 1008, 502);

-- Marketing team
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2027, 1030, '2026-Q1', 63, 4.5, 'Strong marketing leadership. Campaign ROI improved 18% YoY.', 0, '2026-03-31', 1037, 502),
(2028, 1031, '2026-Q1', 62, 4.1, 'Excellent content strategy. Lead gen up 25%.', 0, '2026-03-31', 1030, 502),
(2029, 1032, '2026-Q1', 63, 3.8, 'Digital campaigns performing well. Good analytics skills.', 0, '2026-03-31', 1030, 502),
(2030, 1033, '2026-Q1', 61, 3.9, 'SEO improvements showing results. Organic traffic up 12%.', 0, '2026-03-31', 1030, 502),
(2031, 1034, '2026-Q1', 62, 3.7, 'Good design work. Brand consistency maintained.', 0, '2026-03-31', 1030, 502),
(2032, 1035, '2026-Q1', 63, 4.0, 'Analytics insights valuable for campaign optimization.', 0, '2026-03-31', 1030, 502),
(2033, 1036, '2026-Q1', 60, 3.5, 'New hire. Social media engagement improving.', 0, '2026-03-31', 1030, 502);

-- HR, Finance, Legal, Supply Chain teams
INSERT INTO hr_record (hr_id, employee_id, period, attendance_days, performance_score, performance_summary, warning_count, review_date, reviewer_id, source_id) VALUES
(2034, 1037, '2026-Q1', 64, 4.7, 'Excellent HR leadership. Talent retention strong.', 0, '2026-04-01', 1041, 502),
(2035, 1038, '2026-Q1', 63, 4.2, 'Strong HR management. PIP process improvements implemented.', 0, '2026-04-01', 1037, 502),
(2036, 1039, '2026-Q1', 62, 3.9, 'Good recruiting outcomes. Time-to-hire reduced.', 0, '2026-04-01', 1037, 502),
(2037, 1041, '2026-Q1', 64, 4.8, 'Outstanding financial leadership. Q1 profitability ahead of plan.', 0, '2026-04-01', 1037, 502),
(2038, 1042, '2026-Q1', 63, 4.3, 'Strong finance management. Budget controls effective.', 0, '2026-04-01', 1041, 502),
(2039, 1046, '2026-Q1', 63, 4.6, 'Excellent legal guidance. Compliance initiatives on track.', 0, '2026-04-01', 1037, 502),
(2040, 1048, '2026-Q1', 62, 4.1, 'Good procurement management. Vendor negotiations successful.', 0, '2026-04-01', 1037, 502);

-- ============================================
-- SALES RECORDS (~50 records - deals across Q3 2025 - Q1 2026)
-- ============================================

-- John Tan (1023) - UNDERPERFORMER - low sales
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3001, 1023, 102, '2025-Q3', 'Tech Solutions Renewal', 'SaaS Platform Enterprise', 18500.00, 'closed', 'Tech Solutions Sdn Bhd', 'Kuala Lumpur', '2025-09-15', 514),
(3002, 1023, 102, '2025-Q4', 'Retail Co Renewal', 'SaaS Platform SMB', 8500.00, 'closed', 'Retail Co', 'Kuala Lumpur', '2025-12-08', 503),
(3003, 1023, 102, '2026-Q1', 'Small Business Deal', 'SaaS Platform SMB', 12400.00, 'closed', 'KL Ventures', 'Kuala Lumpur', '2026-03-22', 504),
(3004, 1023, 102, '2026-Q1', 'Enterprise Lead', 'SaaS Platform Enterprise', 0, 'lost', 'Major Corp', 'Kuala Lumpur', NULL, 519),
(3005, 1023, 102, '2026-Q1', 'Mid-Market Opportunity', 'SaaS Platform Professional', 0, 'pipeline', NULL, 'Penang', NULL, 524);

-- Sarah Lim (1020) - Sales Director - high revenue
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3006, 1020, 102, '2025-Q4', 'Enterprise Malaysia Bank', 'SaaS Platform Enterprise', 285000.00, 'closed', 'Malaysia Bank Berhad', 'Kuala Lumpur', '2025-12-15', 503),
(3007, 1020, 102, '2026-Q1', 'Telecom Giant Deal', 'SaaS Platform Enterprise', 420000.00, 'closed', 'Telecom Malaysia', 'Kuala Lumpur', '2026-03-10', 504),
(3008, 1020, 102, '2026-Q1', 'Healthcare Expansion', 'SaaS Platform Enterprise', 195000.00, 'closed', 'Healthcare Group', 'Johor', '2026-03-28', 504);

-- David Wong (1021) - Enterprise focus
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3009, 1021, 102, '2025-Q4', 'Manufacturing Corp', 'SaaS Platform Enterprise', 125000.00, 'closed', 'Manufacturing Corp', 'Penang', '2025-11-20', 503),
(3010, 1021, 102, '2025-Q4', 'Logistics Leader', 'SaaS Platform Enterprise', 98000.00, 'closed', 'Logistics Solutions', 'Kuala Lumpur', '2025-12-10', 503),
(3011, 1021, 102, '2026-Q1', 'Tech Startup Growth', 'SaaS Platform Professional', 65000.00, 'closed', 'TechStart Innovations', 'Cyberjaya', '2026-02-15', 504),
(3012, 1021, 102, '2026-Q1', 'Retail Chain Expansion', 'SaaS Platform Enterprise', 155000.00, 'closed', 'Retail Chain MY', 'Kuala Lumpur', '2026-03-18', 504);

-- Alicia Fernandez (1022) - SMB specialist
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3013, 1022, 102, '2025-Q4', 'SMB Package Deal', 'SaaS Platform SMB', 22000.00, 'closed', 'Business Solutions', 'Johor Bahru', '2025-11-15', 503),
(3014, 1022, 102, '2025-Q4', 'Multi-site SMB', 'SaaS Platform SMB', 35000.00, 'closed', 'Multi-Store Co', 'Penang', '2025-12-05', 503),
(3015, 1022, 102, '2026-Q1', 'SMB Growth Pack', 'SaaS Platform Professional', 42000.00, 'closed', 'Growth Ventures', 'Kuala Lumpur', '2026-02-20', 504),
(3016, 1022, 102, '2026-Q1', 'Startup Bundle', 'SaaS Platform SMB', 18500.00, 'closed', 'StartupHub', 'Cyberjaya', '2026-03-12', 504),
(3017, 1022, 102, '2026-Q1', 'Regional SMB', 'SaaS Platform SMB', 28000.00, 'closed', 'Regional Services', 'Ipoh', '2026-03-25', 504);

-- Muthu Kumar (1024) - Enterprise account manager
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3018, 1024, 102, '2025-Q4', 'Financial Services Renewal', 'SaaS Platform Enterprise', 180000.00, 'closed', 'Financial Services Group', 'Kuala Lumpur', '2025-12-20', 503),
(3019, 1024, 102, '2026-Q1', 'Insurance Expansion', 'SaaS Platform Enterprise', 210000.00, 'closed', 'Insurance Malaysia', 'Kuala Lumpur', '2026-02-28', 504),
(3020, 1024, 102, '2026-Q1', 'Gov Contract Renewal', 'SaaS Platform Enterprise', 145000.00, 'closed', 'Government Agency', 'Putrajaya', '2026-03-15', 504);

-- Nurul Aisyah (1025) - Sales Manager
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3021, 1025, 102, '2025-Q4', 'Strategic Partnership', 'SaaS Platform Enterprise', 320000.00, 'closed', 'Partnership Corp', 'Kuala Lumpur', '2025-11-30', 503),
(3022, 1025, 102, '2026-Q1', 'Education Sector Deal', 'SaaS Platform Professional', 85000.00, 'closed', 'University Group', 'Kuala Lumpur', '2026-02-10', 504);

-- Tan Mei Ling (1026) - SMB sales
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3023, 1026, 102, '2025-Q4', 'SMB New Customer', 'SaaS Platform SMB', 15500.00, 'closed', 'SMB Solutions', 'Penang', '2025-11-25', 503),
(3024, 1026, 102, '2026-Q1', 'SMB Expansion', 'SaaS Platform SMB', 19500.00, 'closed', 'Business Hub', 'Penang', '2026-02-18', 504),
(3025, 1026, 102, '2026-Q1', 'SMB Cross-sell', 'SaaS Platform Professional', 28000.00, 'closed', 'SMB Pro', 'Penang', '2026-03-20', 504),
(3026, 1026, 102, '2026-Q1', 'Regional Deal', 'SaaS Platform SMB', 21000.00, 'closed', 'Regional Business', 'Penang', '2026-03-28', 504);

-- Azman Ibrahim (1027) - Enterprise sales
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3027, 1027, 102, '2025-Q4', 'Pharma Enterprise', 'SaaS Platform Enterprise', 165000.00, 'closed', 'Pharma Solutions', 'Kuala Lumpur', '2025-12-12', 503),
(3028, 1027, 102, '2026-Q1', 'Construction Deal', 'SaaS Platform Enterprise', 135000.00, 'closed', 'Construction Group', 'Johor', '2026-03-05', 504),
(3029, 1027, 102, '2026-Q1', 'Transport Sector', 'SaaS Platform Enterprise', 98000.00, 'closed', 'Transport Malaysia', 'Kuala Lumpur', '2026-03-22', 504);

-- Rebecca Chong (1028) - Sales ops (team deals)
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3030, NULL, 102, '2025-Q4', 'Channel Partner Deal', 'SaaS Platform Enterprise', 250000.00, 'closed', 'Channel Partner Network', 'Multiple', '2025-12-30', 503),
(3031, NULL, 102, '2026-Q1', 'Reseller Agreement', 'SaaS Platform Professional', 180000.00, 'closed', 'Reseller Group', 'Multiple', '2026-03-31', 504);

-- Vincent Lee (1029) - SDR (pipeline generation)
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3032, 1029, 102, '2026-Q1', 'Qualified Lead 1', 'SaaS Platform Professional', 0, 'pipeline', NULL, 'Kuala Lumpur', NULL, 524),
(3033, 1029, 102, '2026-Q1', 'Qualified Lead 2', 'SaaS Platform SMB', 0, 'pipeline', NULL, 'Penang', NULL, 524),
(3034, 1029, 102, '2026-Q1', 'Qualified Lead 3', 'SaaS Platform Enterprise', 0, 'pipeline', NULL, 'Johor', NULL, 524);

-- Additional Q3 2025 deals for context
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3035, 1020, 102, '2025-Q3', 'Enterprise Banking', 'SaaS Platform Enterprise', 195000.00, 'closed', 'Regional Bank', 'Kuala Lumpur', '2025-09-20', 514),
(3036, 1021, 102, '2025-Q3', 'Tech Company Deal', 'SaaS Platform Professional', 75000.00, 'closed', 'Tech Innovations', 'Cyberjaya', '2025-09-25', 514),
(3037, 1022, 102, '2025-Q3', 'SMB Cluster', 'SaaS Platform SMB', 32000.00, 'closed', 'SMB Network', 'Penang', '2025-09-18', 514),
(3038, 1024, 102, '2025-Q3', 'Insurance Renewal', 'SaaS Platform Enterprise', 165000.00, 'closed', 'Insurance Corp', 'Kuala Lumpur', '2025-09-30', 514),
(3039, 1025, 102, '2025-Q3', 'Education Contract', 'SaaS Platform Professional', 92000.00, 'closed', 'College Group', 'Kuala Lumpur', '2025-09-22', 514),
(3040, 1027, 102, '2025-Q3', 'Healthcare System', 'SaaS Platform Enterprise', 125000.00, 'closed', 'Healthcare Provider', 'Johor', '2025-09-28', 514);

-- Lost deals for analysis
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, customer_name, region, close_date, source_id) VALUES
(3041, 1023, 102, '2025-Q4', 'Enterprise Opp Lost', 'SaaS Platform Enterprise', 0, 'lost', 'Enterprise Target', 'Kuala Lumpur', NULL, 519),
(3042, 1023, 102, '2025-Q4', 'Mid-Market Lost', 'SaaS Platform Professional', 0, 'lost', 'Mid Market Co', 'Penang', NULL, 519),
(3043, 1026, 102, '2025-Q4', 'SMB Lost to Competitor', 'SaaS Platform SMB', 0, 'lost', 'SMB Target', 'Ipoh', NULL, 519);

-- ============================================
-- FINANCE RECORDS (~35 records - salaries, budgets, costs)
-- ============================================

-- Salary records for key employees (Q1 2026)
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4001, 102, 1023, '2026-Q1', 'salary', 31500.00, 'MYR', 'personnel', 506), -- John Tan 3 months
(4002, 102, 1020, '2026-Q1', 'salary', 54000.00, 'MYR', 'personnel', 506),
(4003, 102, 1020, '2026-Q1', 'bonus', 15000.00, 'MYR', 'personnel', 506), -- Performance bonus
(4004, 102, 1021, '2026-Q1', 'salary', 34500.00, 'MYR', 'personnel', 506),
(4005, 102, 1021, '2026-Q1', 'commission', 8500.00, 'MYR', 'personnel', 506),
(4006, 102, 1022, '2026-Q1', 'salary', 30600.00, 'MYR', 'personnel', 506),
(4007, 102, 1024, '2026-Q1', 'salary', 41400.00, 'MYR', 'personnel', 506),
(4008, 102, 1025, '2026-Q1', 'salary', 45000.00, 'MYR', 'personnel', 506);

-- Department budget records (Q1 2026)
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4009, 101, NULL, '2026-Q1', 'headcount_cost', 395000.00, 'MYR', 'personnel', 506), -- Engineering total
(4010, 102, NULL, '2026-Q1', 'headcount_cost', 285000.00, 'MYR', 'personnel', 506), -- Sales total
(4011, 103, NULL, '2026-Q1', 'headcount_cost', 182000.00, 'MYR', 'personnel', 506), -- Marketing total
(4012, 104, NULL, '2026-Q1', 'headcount_cost', 135000.00, 'MYR', 'personnel', 506), -- HR total
(4013, 105, NULL, '2026-Q1', 'headcount_cost', 186000.00, 'MYR', 'personnel', 506), -- Finance total
(4014, 106, NULL, '2026-Q1', 'headcount_cost', 88000.00, 'MYR', 'personnel', 506), -- Legal total
(4015, 107, NULL, '2026-Q1', 'headcount_cost', 91000.00, 'MYR', 'personnel', 506); -- Supply Chain total

-- Revenue and costs
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4016, 102, NULL, '2026-Q1', 'revenue', 2680000.00, 'MYR', 'revenue', 506), -- Total sales revenue Q1
(4017, 103, NULL, '2026-Q1', 'marketing_spend', 185000.00, 'MYR', 'operations', 506),
(4018, 107, NULL, '2026-Q1', 'procurement_cost', 125000.00, 'MYR', 'operations', 506),
(4019, 101, NULL, '2026-Q1', 'infrastructure_cost', 85000.00, 'MYR', 'operations', 506), -- AWS, servers, etc.
(4020, NULL, NULL, '2026-Q1', 'office_rent', 65000.00, 'MYR', 'operations', 506),
(4021, NULL, NULL, '2026-Q1', 'utilities', 22000.00, 'MYR', 'operations', 506);

-- Termination and replacement costs (relevant for decision case)
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4022, 104, NULL, '2026-Q1', 'severance_reserve', 150000.00, 'MYR', 'reserves', 506), -- Legal reserve for terminations
(4023, 104, NULL, '2026-Q1', 'replacement_cost_estimate', 45000.00, 'MYR', 'recruiting', 522), -- Average cost to replace sales exec
(4024, 104, NULL, '2026-Q1', 'onboarding_cost_estimate', 12000.00, 'MYR', 'recruiting', 522); -- Training + ramp time

-- Q4 2025 financial records for comparison
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4025, 102, NULL, '2025-Q4', 'revenue', 2450000.00, 'MYR', 'revenue', 515),
(4026, 102, NULL, '2025-Q4', 'headcount_cost', 278000.00, 'MYR', 'personnel', 515),
(4027, 103, NULL, '2025-Q4', 'marketing_spend', 165000.00, 'MYR', 'operations', 515),
(4028, 101, NULL, '2025-Q4', 'infrastructure_cost', 78000.00, 'MYR', 'operations', 515);

-- Individual salary audit records (Q1 2026 - select employees)
INSERT INTO finance_record (finance_id, dept_id, employee_id, period, metric_name, amount, unit, category, source_id) VALUES
(4029, 101, 1003, '2026-Q1', 'salary', 42600.00, 'MYR', 'personnel', 506), -- Priya (DevOps Lead) - star performer
(4030, 101, 1008, '2026-Q1', 'salary', 49500.00, 'MYR', 'personnel', 506), -- Rajesh (Eng Manager)
(4031, 103, 1030, '2026-Q1', 'salary', 49500.00, 'MYR', 'personnel', 506), -- Zara (Marketing Director)
(4032, 104, 1037, '2026-Q1', 'salary', 46500.00, 'MYR', 'personnel', 506), -- Fatimah (HR Director)
(4033, 105, 1041, '2026-Q1', 'salary', 66000.00, 'MYR', 'personnel', 506), -- James (CFO)
(4034, 106, 1046, '2026-Q1', 'salary', 55500.00, 'MYR', 'personnel', 506); -- David Tan (General Counsel)

-- ============================================
-- MARKETING RECORDS (~30 records - campaigns Q3 2025 - Q1 2026)
-- ============================================

-- Q1 2026 campaigns
INSERT INTO marketing_record (marketing_id, period, campaign_name, channel, metric_name, amount, target_audience, source_id) VALUES
(5001, '2026-Q1', 'Enterprise SaaS Growth', 'LinkedIn', 'impressions', 1850000, 'Enterprise IT Decision Makers', 510),
(5002, '2026-Q1', 'Enterprise SaaS Growth', 'LinkedIn', 'clicks', 42500, 'Enterprise IT Decision Makers', 510),
(5003, '2026-Q1', 'Enterprise SaaS Growth', 'LinkedIn', 'conversions', 420, 'Enterprise IT Decision Makers', 510),
(5004, '2026-Q1', 'Enterprise SaaS Growth', 'LinkedIn', 'spend', 98000.00, 'Enterprise IT Decision Makers', 510),
(5005, '2026-Q1', 'SMB Digital Push', 'Google Ads', 'impressions', 2200000, 'SMB Owners Malaysia', 510),
(5006, '2026-Q1', 'SMB Digital Push', 'Google Ads', 'clicks', 68000, 'SMB Owners Malaysia', 510),
(5007, '2026-Q1', 'SMB Digital Push', 'Google Ads', 'conversions', 580, 'SMB Owners Malaysia', 510),
(5008, '2026-Q1', 'SMB Digital Push', 'Google Ads', 'spend', 62000.00, 'SMB Owners Malaysia', 510),
(5009, '2026-Q1', 'Content Marketing', 'Blog/SEO', 'organic_visits', 125000, 'General Tech Audience', 510),
(5010, '2026-Q1', 'Content Marketing', 'Blog/SEO', 'leads', 285, 'General Tech Audience', 510),
(5011, '2026-Q1', 'Email Nurture Campaign', 'Email', 'emails_sent', 45000, 'Existing Leads', 510),
(5012, '2026-Q1', 'Email Nurture Campaign', 'Email', 'conversions', 120, 'Existing Leads', 510),
(5013, '2026-Q1', 'Webinar Series', 'Events', 'attendees', 850, 'Enterprise Prospects', 510),
(5014, '2026-Q1', 'Webinar Series', 'Events', 'qualified_leads', 85, 'Enterprise Prospects', 510),
(5015, '2026-Q1', 'Webinar Series', 'Events', 'spend', 18000.00, 'Enterprise Prospects', 510);

-- Q4 2025 campaigns
INSERT INTO marketing_record (marketing_id, period, campaign_name, channel, metric_name, amount, target_audience, source_id) VALUES
(5016, '2025-Q4', 'Year-End Enterprise Push', 'LinkedIn', 'impressions', 1650000, 'Enterprise Decision Makers', 509),
(5017, '2025-Q4', 'Year-End Enterprise Push', 'LinkedIn', 'clicks', 38000, 'Enterprise Decision Makers', 509),
(5018, '2025-Q4', 'Year-End Enterprise Push', 'LinkedIn', 'conversions', 380, 'Enterprise Decision Makers', 509),
(5019, '2025-Q4', 'Year-End Enterprise Push', 'LinkedIn', 'spend', 85000.00, 'Enterprise Decision Makers', 509),
(5020, '2025-Q4', 'Holiday SMB Campaign', 'Google Ads', 'impressions', 1850000, 'SMB Malaysia', 509),
(5021, '2025-Q4', 'Holiday SMB Campaign', 'Google Ads', 'clicks', 52000, 'SMB Malaysia', 509),
(5022, '2025-Q4', 'Holiday SMB Campaign', 'Google Ads', 'conversions', 450, 'SMB Malaysia', 509),
(5023, '2025-Q4', 'Holiday SMB Campaign', 'Google Ads', 'spend', 55000.00, 'SMB Malaysia', 509),
(5024, '2025-Q4', 'Brand Awareness', 'Social Media', 'impressions', 3200000, 'General Audience', 509),
(5025, '2025-Q4', 'Brand Awareness', 'Social Media', 'engagement', 45000, 'General Audience', 509),
(5026, '2025-Q4', 'Brand Awareness', 'Social Media', 'spend', 25000.00, 'General Audience', 509);

-- Q3 2025 campaigns
INSERT INTO marketing_record (marketing_id, period, campaign_name, channel, metric_name, amount, target_audience, source_id) VALUES
(5027, '2025-Q3', 'Lead Gen Campaign', 'LinkedIn', 'impressions', 1450000, 'Enterprise IT', 520),
(5028, '2025-Q3', 'Lead Gen Campaign', 'LinkedIn', 'conversions', 320, 'Enterprise IT', 520),
(5029, '2025-Q3', 'Lead Gen Campaign', 'LinkedIn', 'spend', 75000.00, 'Enterprise IT', 520),
(5030, '2025-Q3', 'SMB Awareness', 'Google Ads', 'impressions', 1650000, 'SMB Owners', 520),
(5031, '2025-Q3', 'SMB Awareness', 'Google Ads', 'conversions', 380, 'SMB Owners', 520),
(5032, '2025-Q3', 'SMB Awareness', 'Google Ads', 'spend', 48000.00, 'SMB Owners', 520);

-- ============================================
-- SUPPLY CHAIN RECORDS (~30 records - inventory and procurement)
-- ============================================

-- Q1 2026 inventory status
INSERT INTO supply_record (supply_id, period, item_name, item_category, inventory_level, demand_forecast, reorder_point, supplier_name, unit_cost, shortage_flag, source_id) VALUES
(6001, '2026-Q1', 'Dell Latitude Laptops', 'hardware', 12, 18, 15, 'Dell Malaysia', 3800.00, 1, 512),
(6002, '2026-Q1', 'Apple MacBook Pro', 'hardware', 8, 12, 10, 'Apple Authorized', 6500.00, 1, 512),
(6003, '2026-Q1', 'External Monitors 27"', 'hardware', 45, 30, 20, 'Tech Supplies MY', 850.00, 0, 512),
(6004, '2026-Q1', 'Ergonomic Chairs', 'office_supplies', 18, 15, 10, 'Office Furniture Co', 1200.00, 0, 512),
(6005, '2026-Q1', 'Standing Desks', 'office_supplies', 22, 20, 12, 'Office Furniture Co', 2200.00, 0, 512),
(6006, '2026-Q1', 'AWS Credits', 'licenses', 850000, 950000, 800000, 'Amazon Web Services', 1.00, 1, 512),
(6007, '2026-Q1', 'GitHub Enterprise Licenses', 'licenses', 50, 55, 45, 'GitHub', 21.00, 1, 512),
(6008, '2026-Q1', 'Slack Business Licenses', 'licenses', 55, 55, 50, 'Slack Technologies', 12.50, 0, 512),
(6009, '2026-Q1', 'Zoom Enterprise Licenses', 'licenses', 55, 55, 50, 'Zoom Video', 20.00, 0, 512),
(6010, '2026-Q1', 'Office Supplies Package', 'office_supplies', 180, 150, 100, 'Stationery Mart', 25.00, 0, 512),
(6011, '2026-Q1', 'Server Rack Units', 'hardware', 3, 5, 4, 'IT Infrastructure MY', 18500.00, 1, 512),
(6012, '2026-Q1', 'Network Switches', 'hardware', 8, 10, 6, 'Cisco Malaysia', 4200.00, 1, 512),
(6013, '2026-Q1', 'UPS Backup Systems', 'hardware', 5, 6, 4, 'APC Malaysia', 3500.00, 1, 512),
(6014, '2026-Q1', 'Wireless Access Points', 'hardware', 15, 12, 8, 'Ubiquiti MY', 850.00, 0, 512),
(6015, '2026-Q1', 'Security Cameras', 'hardware', 12, 10, 6, 'Security Solutions', 950.00, 0, 512);

-- Q4 2025 inventory comparison
INSERT INTO supply_record (supply_id, period, item_name, item_category, inventory_level, demand_forecast, reorder_point, supplier_name, unit_cost, shortage_flag, source_id) VALUES
(6016, '2025-Q4', 'Dell Latitude Laptops', 'hardware', 18, 20, 15, 'Dell Malaysia', 3750.00, 0, 511),
(6017, '2025-Q4', 'Apple MacBook Pro', 'hardware', 14, 15, 10, 'Apple Authorized', 6400.00, 0, 511),
(6018, '2025-Q4', 'External Monitors 27"', 'hardware', 35, 30, 20, 'Tech Supplies MY', 820.00, 0, 511),
(6019, '2025-Q4', 'AWS Credits', 'licenses', 920000, 900000, 800000, 'Amazon Web Services', 1.00, 0, 511),
(6020, '2025-Q4', 'GitHub Enterprise Licenses', 'licenses', 48, 50, 45, 'GitHub', 21.00, 0, 511),
(6021, '2025-Q4', 'Slack Business Licenses', 'licenses', 52, 55, 50, 'Slack Technologies', 12.50, 0, 511),
(6022, '2025-Q4', 'Office Supplies Package', 'office_supplies', 250, 200, 100, 'Stationery Mart', 25.00, 0, 511);

-- Vendor performance tracking
INSERT INTO supply_record (supply_id, period, item_name, item_category, inventory_level, demand_forecast, reorder_point, supplier_name, unit_cost, shortage_flag, source_id) VALUES
(6023, '2026-Q1', 'Vendor Perf: Dell', 'vendor_metric', 0, 0, 0, 'Dell Malaysia', 0, 0, 521),
(6024, '2026-Q1', 'Vendor Perf: Apple', 'vendor_metric', 0, 0, 0, 'Apple Authorized', 0, 0, 521),
(6025, '2026-Q1', 'Vendor Perf: AWS', 'vendor_metric', 0, 0, 0, 'Amazon Web Services', 0, 1, 521), -- AWS credit shortage noted
(6026, '2026-Q1', 'Vendor Perf: GitHub', 'vendor_metric', 0, 0, 0, 'GitHub', 0, 0, 521),
(6027, '2026-Q1', 'Vendor Perf: Office Furn', 'vendor_metric', 0, 0, 0, 'Office Furniture Co', 0, 0, 521);

-- Critical procurement needs (flagged for decision engine)
INSERT INTO supply_record (supply_id, period, item_name, item_category, inventory_level, demand_forecast, reorder_point, supplier_name, unit_cost, shortage_flag, source_id) VALUES
(6028, '2026-Q2-Forecast', 'Emergency Laptop Order', 'hardware', 0, 25, 15, 'Dell Malaysia', 3800.00, 1, 512),
(6029, '2026-Q2-Forecast', 'AWS Credit Top-up', 'licenses', 0, 200000, 100000, 'Amazon Web Services', 1.00, 1, 512),
(6030, '2026-Q2-Forecast', 'Network Expansion Kit', 'hardware', 0, 8, 5, 'Cisco Malaysia', 4200.00, 1, 512);

-- ============================================
-- LEGAL RECORDS (~12 policies)
-- ============================================

INSERT INTO legal_record (legal_id, policy_category, policy_name, rule_text, effective_date, region, source_id) VALUES
(7001, 'termination', 'Performance-Based Termination Policy', 
'Employees may be terminated for cause after two consecutive underperformance reviews (performance score < 2.5/5.0) AND completion of a mandatory 60-day Performance Improvement Plan (PIP). Termination must be approved by department head and HR Director. Severance: 1 month base salary per year of service, minimum RM 20,000, maximum RM 100,000.', 
'2025-06-01', 'Malaysia', 507),

(7002, 'termination', 'Severance Calculation Guidelines', 
'Severance formula: (Years of Service × 1 month base salary) + (Unused leave days × daily rate). Minimum: RM 20,000. Maximum: RM 100,000. Payment within 30 days of exit date. EPF and SOCSO contributions settled as per Malaysian law.', 
'2025-06-15', 'Malaysia', 517),

(7003, 'termination', 'Immediate Termination - Misconduct', 
'Immediate termination allowed without PIP for: (1) Gross misconduct, (2) Fraud or theft, (3) Violence or harassment, (4) Breach of confidentiality, (5) Criminal conviction. No severance required if documented evidence exists. Must involve Legal and HR approval.', 
'2025-06-01', 'Malaysia', 507),

(7004, 'hiring', 'Replacement Hiring Policy', 
'Replacement hires for terminated employees require: (1) Department head justification, (2) Budget approval from Finance, (3) HR screening process (minimum 3 weeks). Estimated replacement cost: RM 35,000 - RM 55,000 including recruitment fees, onboarding, and 3-month ramp time productivity loss.', 
'2025-06-01', 'Malaysia', 522),

(7005, 'performance', 'Performance Improvement Plan (PIP) Guidelines', 
'PIP duration: 60 days minimum, 90 days maximum. Must include: (1) Specific measurable goals, (2) Weekly check-ins with manager, (3) Mid-point review at 30 days, (4) Final assessment. Success criteria must be documented. PIP completion required before performance termination.', 
'2025-07-15', 'Malaysia', 508),

(7006, 'compliance', 'Malaysian Employment Act Compliance', 
'All terminations must comply with Employment Act 1955. Notice period: 1 month for employees with > 2 years service. Termination must not be discriminatory (race, religion, gender, disability). Written termination letter required. Employee entitled to appeal within 14 days.', 
'2025-06-01', 'Malaysia', 507),

(7007, 'expansion', 'Singapore Market Expansion Requirements', 
'To operate in Singapore: (1) Register Pte Ltd entity (paid-up capital min SGD 1), (2) Appoint local director (Singapore resident), (3) Comply with Employment Act (Singapore), (4) Data residency: local hosting required for government clients, (5) Tax: 17% corporate tax, (6) Setup cost estimate: SGD 80,000 - SGD 120,000.', 
'2025-11-20', 'Singapore', 516),

(7008, 'compliance', 'Data Privacy and PDPA Compliance', 
'Personal Data Protection Act (PDPA) 2010 compliance mandatory. Employee data retention: 7 years post-exit. Customer data: consent-based processing only. Data breach notification: within 72 hours. PDPA fines up to RM 500,000. Annual compliance audit required.', 
'2025-08-01', 'Malaysia', 525),

(7009, 'IP', 'Intellectual Property Ownership', 
'All work product created by employees during employment is company property. Non-compete: 6 months post-exit for senior roles. Confidentiality obligations survive termination indefinitely. Source code, customer lists, and business plans are protected trade secrets.', 
'2025-06-01', 'Malaysia', 507),

(7010, 'contracts', 'Customer Contract Standards', 
'Enterprise contracts > RM 100,000 require Legal review. Standard terms: 12-month minimum, auto-renewal with 60-day notice, payment terms Net-30, liability cap at 12 months fees. Government contracts require additional compliance clauses.', 
'2025-06-01', 'Malaysia', 507),

(7011, 'procurement', 'Vendor Contract Requirements', 
'Vendor contracts > RM 50,000 require Legal approval. Must include: (1) SLA terms, (2) Liability clauses, (3) Termination rights, (4) Data protection terms. Emergency procurement (< 2 weeks lead time) requires CFO approval for spend > RM 100,000.', 
'2025-06-01', 'Malaysia', 507),

(7012, 'acquisition', 'M&A Due Diligence Policy', 
'Acquisitions > RM 2M require: (1) Board approval, (2) Legal due diligence (minimum 4 weeks), (3) Financial audit, (4) Antitrust review if combined market share > 25%. Standard reps & warranties required. Escrow: 10-15% of purchase price for 12 months.', 
'2025-06-01', 'Malaysia', 507);

-- ============================================
-- DECISION CASES (3 main cases for demo)
-- ============================================

INSERT INTO decision_case (case_id, question, context, target_type, target_id, status, submitted_by, created_at) VALUES
(8001, 'Should we terminate employee John Tan (ID 1023)?', 
'Sales executive with declining performance over 2 quarters. HR flagged for review. Sales team morale reportedly affected.', 
'employee', 1023, 'completed', 'Sarah Lim (Sales Director)', '2026-04-15 10:30:00'),

(8002, 'Should we expand to Singapore market?', 
'Received 3 inbound enterprise leads from Singapore in Q1. No local presence currently. Competitor entered SG market last quarter.', 
'market_expansion', NULL, 'completed', 'James Lim (CFO)', '2026-04-16 14:20:00'),

(8003, 'Should we emergency-procure additional AWS credits?', 
'Current AWS credit inventory below reorder point. Forecast shows 20% shortage risk by month-end. Infrastructure team flagged potential service disruption.', 
'procurement', NULL, 'completed', 'Azman Yusof (Procurement)', '2026-04-17 09:15:00');

-- ============================================
-- CASE EVIDENCE (linking cases to records)
-- ============================================

-- Case 8001: Fire John Tan (employee 1023)
INSERT INTO case_evidence (evidence_id, case_id, source_table, record_id, relevance_score, retrieval_method, notes) VALUES
(9001, 8001, 'hr_record', 2001, 0.92, 'sql_query', 'Q3 2025 underperformance review, score 2.8/5'),
(9002, 8001, 'hr_record', 2002, 0.98, 'sql_query', 'Q4 2025 declining performance, warning issued, score 2.1/5'),
(9003, 8001, 'hr_record', 2003, 0.99, 'sql_query', 'Q1 2026 continued underperformance, score 2.0/5, PIP recommended'),
(9004, 8001, 'sales_record', 3001, 0.88, 'sql_query', 'Q3 2025 sales: RM 18,500 (below team average)'),
(9005, 8001, 'sales_record', 3002, 0.90, 'sql_query', 'Q4 2025 sales: RM 8,500 (bottom 10% of team)'),
(9006, 8001, 'sales_record', 3003, 0.93, 'sql_query', 'Q1 2026 sales: RM 12,400 (bottom 8% of team)'),
(9007, 8001, 'sales_record', 3004, 0.85, 'sql_query', 'Q1 2026 lost enterprise deal'),
(9008, 8001, 'legal_record', 7001, 0.95, 'vector_search', 'Performance termination policy: PIP required'),
(9009, 8001, 'legal_record', 7002, 0.92, 'vector_search', 'Severance calculation: min RM 20k for 2.5 years service'),
(9010, 8001, 'legal_record', 7005, 0.90, 'vector_search', 'PIP guidelines: 60-day minimum duration'),
(9011, 8001, 'finance_record', 4001, 0.80, 'sql_query', 'Current salary cost: RM 10,500/month'),
(9012, 8001, 'finance_record', 4022, 0.78, 'sql_query', 'Severance reserve available: RM 150k'),
(9013, 8001, 'finance_record', 4023, 0.85, 'sql_query', 'Replacement cost estimate: RM 45k'),
(9014, 8001, 'finance_record', 4024, 0.82, 'sql_query', 'Onboarding cost estimate: RM 12k'),
(9015, 8001, 'sales_record', 3006, 0.70, 'sql_query', 'Comparison: Sarah Lim Q1 revenue RM 900k (top performer)');

-- Case 8002: Singapore expansion
INSERT INTO case_evidence (evidence_id, case_id, source_table, record_id, relevance_score, retrieval_method, notes) VALUES
(9016, 8002, 'legal_record', 7007, 0.98, 'vector_search', 'Singapore legal requirements: Pte Ltd, local director, setup cost SGD 80-120k'),
(9017, 8002, 'finance_record', 4016, 0.85, 'sql_query', 'Q1 2026 revenue baseline: RM 2.68M'),
(9018, 8002, 'marketing_record', 5001, 0.80, 'sql_query', 'Enterprise campaign reach: 1.85M impressions'),
(9019, 8002, 'marketing_record', 5003, 0.82, 'sql_query', 'Enterprise campaign conversions: 420 leads'),
(9020, 8002, 'finance_record', 4019, 0.75, 'sql_query', 'Current infrastructure cost: RM 85k/quarter (capacity for expansion)');

-- Case 8003: AWS credit procurement
INSERT INTO case_evidence (evidence_id, case_id, source_table, record_id, relevance_score, retrieval_method, notes) VALUES
(9021, 8003, 'supply_record', 6006, 0.99, 'sql_query', 'AWS credits: 850k current vs 950k forecast, shortage flagged'),
(9022, 8003, 'supply_record', 6019, 0.88, 'sql_query', 'Q4 2025 comparison: 920k available, no shortage'),
(9023, 8003, 'supply_record', 6025, 0.85, 'sql_query', 'Vendor performance: AWS shortage trend noted'),
(9024, 8003, 'finance_record', 4019, 0.90, 'sql_query', 'Current infrastructure budget: RM 85k/quarter'),
(9025, 8003, 'legal_record', 7011, 0.80, 'vector_search', 'Emergency procurement policy: CFO approval for > RM 100k');

-- ============================================
-- DECISION OUTPUTS (final manager verdicts)
-- ============================================

INSERT INTO decision_output (decision_id, case_id, recommendation, risk_level, confidence_score, rationale, conservative_view, aggressive_view, manager_persona) VALUES
(10001, 8001,
'DO NOT TERMINATE — Initiate mandatory 60-day PIP with measurable exit criteria',
'Medium',
78,
'**HR Agent Analysis:** Employee 1023 (John Tan) shows sustained underperformance across two consecutive quarters (Q4 2025: score 2.1/5, Q1 2026: score 2.0/5). Two warnings issued. Attendance issues emerging (7 absence days Q4). However, Performance Improvement Plan (PIP) has NOT been initiated, which is mandatory per company policy (Legal Record 7001, 7005).

**Sales Agent Analysis:** Revenue contribution critically low: Q3 2025 (RM 18.5k), Q4 2025 (RM 8.5k), Q1 2026 (RM 12.4k). This places employee in bottom 8% of sales team. Comparison: top performer Sarah Lim generated RM 900k in Q1 2026. Lost 1 enterprise deal, pipeline thin (only 1 active opportunity). Team morale impact noted in reviews.

**Legal Agent Analysis:** Termination for performance is permitted ONLY after: (1) Two consecutive underperformance reviews (SATISFIED), (2) Completion of 60-day PIP (NOT SATISFIED). Company policy (Legal 7001) mandates PIP before termination. Severance cost: minimum RM 20,000 for 2.5 years of service (Legal 7002). Risk: wrongful termination claim if PIP skipped.

**Finance Agent Analysis:** Current cost: RM 10,500/month salary. Termination cost breakdown: Severance RM 20k + Replacement RM 45k + Onboarding RM 12k = **Total RM 77k one-time cost**. Savings: RM 10.5k/month if not replaced, but realistically need backfill. Break-even: 7.3 months. Replacement ramp time: 3 months to productivity.

**Manager Decision (Conservative Stance):**
Short-term termination cost (RM 77k total) + 3-month productivity gap during replacement ramp outweighs immediate savings. Legal risk of wrongful termination without PIP completion is significant. **Recommendation: Initiate mandatory 60-day PIP immediately with clear metrics: (1) Close minimum 2 deals, (2) Generate RM 50k revenue, (3) Zero customer complaints, (4) Improve attendance to < 2 absence days/month.** If PIP fails, termination becomes legally justified with full documentation. This preserves optionality while protecting company from legal exposure.',

'Do NOT terminate - initiate PIP first. Legal risk too high without PIP completion. Replacement cost (RM 77k) + ramp time (3 months) outweighs short-term savings. 60-day PIP provides documented exit path if performance does not improve. Conservative approach protects company legally.',

'Terminate immediately - sustained underperformance hurts team morale and revenue. Bottom 8% performer for 2 quarters is clear cause. Legal policy technically allows termination after 2 reviews. Severance cost (RM 20k) is acceptable. Replacement can be sourced from active pipeline within 4 weeks. Aggressive action sends clear performance message to sales team.',

'conservative');

INSERT INTO decision_output (decision_id, case_id, recommendation, risk_level, confidence_score, rationale, conservative_view, aggressive_view, manager_persona) VALUES
(10002, 8002,
'EXPAND — Phased entry: Start with 2-person remote sales pod (6 months), then full office if KPIs hit',
'Low',
82,
'**Market Agent Analysis:** Singapore TAM for SaaS estimated at USD 180M (MYR 850M+). Inbound signal strength: 3 enterprise leads in Q1 2026 WITHOUT local presence indicates demand. Competitor (Beta Corp) entered SG market Q4 2025, creating urgency. Regional expansion aligns with growth strategy.

**Legal Agent Analysis:** Singapore requirements (Legal 7007): (1) Pte Ltd registration (min SGD 1 paid-up capital), (2) Local director required, (3) Employment Act compliance, (4) Data residency for gov clients. Setup cost: SGD 80-120k (RM 380-570k). Timeline: 8-12 weeks for full entity setup. Legal complexity: MODERATE (manageable with local counsel).

**Finance Agent Analysis:** Current Q1 revenue baseline: RM 2.68M. Full office setup cost: RM 1.8M (year 1) includes: office lease, 5 staff, local entity, compliance. Break-even projection: 18 months if 5 enterprise deals closed (avg RM 150k each). Current cash reserves: adequate to support expansion. Alternative: remote sales pod cost RM 400k (2 sales staff + travel) for 6-month pilot.

**Marketing Agent Analysis:** Q1 2026 enterprise campaign generated 420 conversions, showing demand for enterprise SaaS in region. LinkedIn reach: 1.85M impressions. Digital infrastructure ready to support SG market targeting. Estimated marketing spend for SG launch: RM 120k (Q2-Q3).

**Manager Decision (Balanced - Phased Approach):**
Inbound demand signals are REAL (3 enterprise leads) but unproven at scale. **Recommendation: Phase 1 (6 months) - Launch remote sales pod:** (1) Hire 2 sales executives (work from Malaysia, target SG market), (2) Monthly SG travel for client meetings, (3) Target: close 2 enterprise deals (RM 300k revenue), (4) Cost: RM 400k. **Phase 2 (conditional) - Full office:** IF Phase 1 hits KPIs (2 deals + RM 300k revenue), proceed with full Pte Ltd setup and local office (RM 1.8M). This approach: (1) Validates market demand, (2) Limits downside to RM 400k vs RM 1.8M, (3) Preserves fast-scaling path if validated, (4) Mitigates competitor first-mover advantage.',

'Start with remote sales pod only (RM 400k). Validate demand for 6 months before committing RM 1.8M to full office. Inbound leads are promising but unproven. Phased approach limits financial risk while testing market. Can scale quickly if KPIs hit.',

'Launch full office immediately (RM 1.8M). First-mover advantage critical - competitor already in market. 3 inbound leads without presence proves demand. Speed wins in market expansion. 18-month break-even is acceptable. Commit fully to capture market share.',

'balanced');

INSERT INTO decision_output (decision_id, case_id, recommendation, risk_level, confidence_score, rationale, conservative_view, aggressive_view, manager_persona) VALUES
(10003, 8003,
'APPROVE — Emergency-procure 200,000 AWS credits immediately (RM 200k spend)',
'High',
91,
'**Supply Chain Agent Analysis:** Current AWS credit inventory: 850,000. Demand forecast: 950,000 (Q1 actual usage tracking). Shortage gap: 100,000 credits (11% deficit). Reorder point: 800,000 (BREACHED). Infrastructure team flagged potential service disruption if credits run out. Historical trend: Q4 2025 inventory was 920,000 (healthy), indicating Q1 usage spike. Supplier: Amazon Web Services (reliable, 48-hour delivery for credit top-ups).

**Operations Agent (Engineering):** AWS credits are mission-critical for SaaS infrastructure. Current burn rate: ~950k credits/quarter (increasing due to customer growth). If credits run out: (1) Service downtime, (2) Customer SLA breaches, (3) Revenue loss, (4) Reputational damage. No alternative cloud provider configured (migration would take 8-12 weeks). Downtime cost estimate: RM 400k/week (based on revenue impact + SLA penalties).

**Finance Agent Analysis:** Current infrastructure budget: RM 85k/quarter (Finance 4019). Emergency procurement cost: RM 200k for 200,000 AWS credits (unit cost RM 1/credit). This exceeds quarterly budget by RM 115k BUT cost of inaction (service downtime) is RM 400k/week. Break-even: avoiding even 1 day of downtime justifies procurement. Legal policy (Legal 7011): emergency procurement > RM 100k requires CFO approval.

**Legal Agent Analysis:** Emergency procurement policy (Legal 7011) allows fast-track approval for spend > RM 100k if: (1) Lead time < 2 weeks, (2) CFO approves, (3) Service disruption risk. All conditions met. Standard vendor contract with AWS in place. No additional legal barriers.

**Manager Decision (Aggressive - Immediate Action):**
Risk of inaction (service downtime, SLA breaches, customer churn) FAR EXCEEDS procurement cost. **Recommendation: APPROVE emergency procurement of 200,000 AWS credits immediately (RM 200k).** Actions: (1) CFO approval obtained, (2) AWS order placed today (48-hour delivery), (3) Engineering team to implement usage monitoring alerts, (4) Finance team to review Q2 infrastructure budget (increase by 20% to RM 102k/quarter), (5) Supply Chain to conduct root cause analysis: Why did usage spike 11% in Q1? Is this a trend or anomaly? **This is the SECOND shortage in Q1 (also seen in hardware/licenses), indicating systemic procurement process issue that needs addressing.**',

'Approve emergency procurement but order only 150,000 credits (RM 150k) to cover immediate gap. Negotiate with AWS for better bulk pricing. Review Q1 usage spike before committing to higher baseline. Cost-conscious approach.',

'Approve full 200,000 credit procurement immediately (RM 200k). Service disruption risk is unacceptable. Downtime cost (RM 400k/week) dwarfs procurement cost. Speed critical - order today, no negotiations. Also flag systemic procurement issue: this is Q1 shortage #2, needs process overhaul.',

'aggressive');

-- ============================================
-- DATA INTEGRITY VERIFICATION QUERIES
-- ============================================

-- These queries validate cross-table relationships
-- (Not executed, but documented for testing)

/*
-- Verify all foreign keys resolve
SELECT 'hr_record' as table_name, COUNT(*) as orphaned_fks
FROM hr_record h
LEFT JOIN employee e ON h.employee_id = e.employee_id
WHERE e.employee_id IS NULL;

-- Verify sales attribution
SELECT e.name, COUNT(s.sales_id) as deal_count, SUM(s.amount) as total_revenue
FROM employee e
LEFT JOIN sales_record s ON e.employee_id = s.employee_id
WHERE e.dept_id = 102
GROUP BY e.employee_id
ORDER BY total_revenue DESC;

-- Verify case evidence linking
SELECT c.case_id, c.question, COUNT(ce.evidence_id) as evidence_count
FROM decision_case c
LEFT JOIN case_evidence ce ON c.case_id = ce.case_id
GROUP BY c.case_id;
*/
