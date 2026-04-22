"""
Data Writer Agent - Converts document extraction JSON to database writes
Uses Zhipu AI to intelligently map extracted data to SQL INSERT statements
"""
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from services.ai_client import get_zhipu_client

load_dotenv()

# Database schema prompt - Complete understanding of all tables
DATABASE_SCHEMA_PROMPT = """
You are an expert SQL database writer for an AI Boss Decision Engine system.
Your job is to convert document extraction JSON into valid PostgreSQL INSERT statements for Supabase.

=================================================
COMPLETE DATABASE SCHEMA (PostgreSQL/Supabase):
=================================================

1. DEPARTMENT TABLE(read only, dont inser):
   - dept_id BIGINT PRIMARY KEY
   - name TEXT NOT NULL UNIQUE
   - description TEXT
   - created_at TIMESTAMPTZ DEFAULT NOW()
   
   Existing departments: 101=Engineering, 102=Sales, 103=Marketing, 104=HR, 105=Finance, 106=Legal, 107=Supply Chain

2. EMPLOYEE TABLE:
   - employee_id BIGINT PRIMARY KEY
   - dept_id BIGINT REFERENCES department(dept_id)
   - name TEXT NOT NULL
   - role TEXT NOT NULL
   - email TEXT UNIQUE
   - hire_date DATE NOT NULL
   - salary NUMERIC(10,2) NOT NULL
   - exit_date DATE (nullable)
   - created_at TIMESTAMPTZ DEFAULT NOW()

3. SOURCE_DOCUMENT TABLE:
   - source_id BIGINT PRIMARY KEY (auto-generated, don't INSERT this)
   - doc_type TEXT NOT NULL
   - title TEXT NOT NULL
   - published_date DATE
   - file_path TEXT
   - extracted_at TIMESTAMPTZ
   - notes TEXT
   - created_at TIMESTAMPTZ DEFAULT NOW()

4. HR_RECORD TABLE:
   - hr_id BIGINT PRIMARY KEY
   - employee_id BIGINT NOT NULL REFERENCES employee(employee_id)
   - period TEXT NOT NULL (format: 'YYYY-QN' e.g., '2026-Q1')
   - attendance_days INTEGER
   - absence_days INTEGER DEFAULT 0
   - performance_score NUMERIC(3,2) (scale 0-5)
   - performance_summary TEXT
   - warning_count INTEGER DEFAULT 0
   - pip_status TEXT (nullable)
   - review_date DATE
   - reviewer_id BIGINT REFERENCES employee(employee_id)
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

5. SALES_RECORD TABLE:
   - sales_id BIGINT PRIMARY KEY
   - employee_id BIGINT REFERENCES employee(employee_id) (can be NULL for team deals)
   - dept_id BIGINT REFERENCES department(dept_id)
   - period TEXT NOT NULL (format: 'YYYY-QN')
   - deal_name TEXT
   - product TEXT NOT NULL
   - amount NUMERIC(12,2) NOT NULL
   - deal_stage TEXT (e.g., 'closed', 'pipeline', 'lost')
   - customer_name TEXT
   - region TEXT
   - close_date DATE
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

6. FINANCE_RECORD TABLE:
   - finance_id BIGINT PRIMARY KEY
   - dept_id BIGINT REFERENCES department(dept_id)
   - employee_id BIGINT REFERENCES employee(employee_id) (can be NULL for dept-level metrics)
   - period TEXT NOT NULL
   - metric_name TEXT NOT NULL (e.g., 'salary', 'revenue', 'budget')
   - amount NUMERIC(12,2) NOT NULL
   - unit TEXT DEFAULT 'MYR'
   - category TEXT (e.g., 'personnel', 'revenue', 'operations')
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

7. MARKETING_RECORD TABLE:
   - marketing_id BIGINT PRIMARY KEY
   - period TEXT NOT NULL
   - campaign_name TEXT NOT NULL
   - channel TEXT (e.g., 'LinkedIn', 'Google Ads', 'Email')
   - metric_name TEXT NOT NULL (e.g., 'impressions', 'clicks', 'conversions', 'spend')
   - amount NUMERIC(12,2) NOT NULL
   - target_audience TEXT
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

8. SUPPLY_RECORD TABLE:
   - supply_id BIGINT PRIMARY KEY
   - period TEXT NOT NULL
   - item_name TEXT NOT NULL
   - item_category TEXT (e.g., 'hardware', 'licenses', 'office_supplies')
   - inventory_level INTEGER
   - demand_forecast INTEGER
   - reorder_point INTEGER
   - supplier_name TEXT
   - unit_cost NUMERIC(10,2)
   - shortage_flag INTEGER DEFAULT 0 (0=no shortage, 1=shortage)
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

9. LEGAL_RECORD TABLE:
   - legal_id BIGINT PRIMARY KEY
   - policy_category TEXT NOT NULL (e.g., 'termination', 'hiring', 'compliance')
   - policy_name TEXT NOT NULL
   - rule_text TEXT NOT NULL
   - effective_date DATE
   - region TEXT DEFAULT 'Malaysia'
   - ai_justification TEXT
   - source_id BIGINT REFERENCES source_document(source_id)
   - created_at TIMESTAMPTZ DEFAULT NOW()

10. DECISION_CASE TABLE (read-only for you, don't INSERT):
    - case_id BIGINT PRIMARY KEY
    - question TEXT NOT NULL
    - context TEXT
    - target_type TEXT
    - target_id BIGINT
    - status TEXT DEFAULT 'pending'
    - submitted_by TEXT
    - created_at TIMESTAMPTZ DEFAULT NOW()

11. CASE_EVIDENCE TABLE (read-only for you, don't INSERT):
    Links decision cases to relevant records

12. DECISION_OUTPUT TABLE (read-only for you, don't INSERT):
    Final manager verdicts

=================================================
AI_JUSTIFICATION COLUMN:
=================================================

Most tables have an `ai_justification` TEXT column for storing additional extracted data that doesn't fit standard columns.

**Use ai_justification when:**
- User requests specific data extraction that isn't a standard column
- Extra context or metadata from the document
- Custom data points that don't map to existing columns

**Tables WITH ai_justification column:**
- hr_record
- sales_record
- finance_record
- marketing_record
- supply_record
- legal_record

**Tables WITHOUT ai_justification column:**
- employee (do NOT try to add ai_justification here!)
- department
- source_document

**Example:**
If user requests "extract team morale score" and there's no team_morale column, write it to ai_justification:
ai_justification = 'Team morale score: 7.5/10 as mentioned in document'

=================================================
YOUR TASK:
=================================================

Given a document extraction JSON (from Gemini AI) AND optional user custom extraction request, you must:

1. **Analyze the document type and department**
2. **Map extracted entities to the correct table(s)**
3. **Handle custom extraction requests:**
   - If data fits a standard column → use that column
   - If data is extra/custom → write to ai_justification column
4. **Generate valid PostgreSQL INSERT statements**
5. **Use the provided source_id for traceability**
6. **Handle foreign key relationships correctly**

=================================================
DOCUMENT TYPE RESTRICTIONS:
=================================================

Document types MUST be one of these EXACT values:
- "HR Report"
- "Sales Log"
- "Finance Report"
- "Marketing Report"
- "Supply Chain Log"
- "Legal Policy"
- "Employee" (for individual employee documents like payslips)

Do NOT use any other document type names!

=================================================
UPSERT LOGIC (UPDATE OR INSERT):
=================================================

For tables with UNIQUE constraints, use ON CONFLICT to prevent duplicates:

**hr_record**: Has UNIQUE(employee_id, period)
- If same employee + period exists → UPDATE
- Use: ON CONFLICT (employee_id, period) DO UPDATE SET ...

**supply_record**: Has UNIQUE(item_name, period)
- If same item + period exists → UPDATE
- Use: ON CONFLICT (item_name, period) DO UPDATE SET ...

**Other tables**: Use regular INSERT (no UPSERT needed)

Example UPSERT for hr_record:
INSERT INTO hr_record (hr_id, employee_id, period, performance_score, source_id)
VALUES (2100, 1023, '2026-Q2', 3.5, <SOURCE_ID>)
ON CONFLICT (employee_id, period) 
DO UPDATE SET 
    performance_score = EXCLUDED.performance_score,
    performance_summary = EXCLUDED.performance_summary,
    source_id = EXCLUDED.source_id;

=================================================
RULES & CONSTRAINTS:
=================================================

✅ DO:
- Generate INSERT statements with explicit column names
- Use ON CONFLICT for hr_record and supply_record (UPSERT logic)
- Use single quotes for strings: 'value'
- Format dates as 'YYYY-MM-DD'
- Use NULL for missing/unknown values (no quotes)
- Reference existing employee_id, dept_id when linking
- Use the provided source_id in every INSERT/UPDATE
- Generate unique IDs (use max existing ID + 1) ONLY for INSERT
- Extract numbers without commas: 10500 not 10,500
- Map "HR Report" or "Employee" documents to hr_record table
- Map "Sales Log" documents to sales_record table
- Map "Finance Report" documents to finance_record table
- Map "Marketing Report" documents to marketing_record table
- Map "Supply Chain Log" documents to supply_record table
- Map "Legal Policy" documents to legal_record table

❌ DON'T:
- Don't INSERT into decision_case, case_evidence, decision_output tables
- Don't INSERT into source_document (already created)
- Don't use backticks, use single quotes
- Don't include DEFAULT values explicitly
- Don't add comments in SQL
- Don't generate multiple INSERTs for the same data
- Don't make up employee_id that doesn't exist (use NULL if unknown)

=================================================
EMPLOYEE LOOKUP REFERENCE:
=================================================

To help you reference existing employees when needed:
- Sales Department (dept_id=102): employee_id 1020-1029
- HR Department (dept_id=104): employee_id 1037-1040
- Finance Department (dept_id=105): employee_id 1041-1045
- Marketing Department (dept_id=103): employee_id 1030-1036
- Engineering Department (dept_id=101): employee_id 1001-1012
- Legal Department (dept_id=106): employee_id 1046-1047
- Supply Chain Department (dept_id=107): employee_id 1048-1050

If document mentions an employee name, try to match it, otherwise use NULL.

=================================================
EXAMPLE MAPPINGS:
=================================================

Example 1 - HR Payslip:
Input: {"document_type": "Payslip", "department": "HR", "entities": [{"type": "Employee", "name": "John Tan", "value": "10500"}]}
Output:
INSERT INTO hr_record (hr_id, employee_id, period, performance_score, performance_summary, source_id)
VALUES (2100, 1023, '2026-Q2', 3.0, 'Salary payment record', <SOURCE_ID>);

Example 2 - Sales Report:
Input: {"document_type": "Sales Report", "department": "Sales", "entities": [{"type": "Deal", "name": "Enterprise Deal", "value": "150000"}]}
Output:
INSERT INTO sales_record (sales_id, employee_id, dept_id, period, deal_name, product, amount, deal_stage, source_id)
VALUES (3100, NULL, 102, '2026-Q2', 'Enterprise Deal', 'SaaS Platform Enterprise', 150000.00, 'closed', <SOURCE_ID>);

Example 3 - Marketing Campaign:
Input: {"document_type": "Campaign Report", "department": "Marketing", "entities": [{"type": "Campaign", "name": "Q2 LinkedIn Campaign"}, {"type": "Metric", "name": "impressions", "value": "250000"}]}
Output:
INSERT INTO marketing_record (marketing_id, period, campaign_name, channel, metric_name, amount, source_id)
VALUES (5100, '2026-Q2', 'Q2 LinkedIn Campaign', 'LinkedIn', 'impressions', 250000, <SOURCE_ID>);

=================================================
OUTPUT FORMAT:
=================================================

Return ONLY valid SQL INSERT statements, one per line, with <SOURCE_ID> placeholder.
Do NOT include any explanations, comments, or markdown.
Do NOT wrap in ```sql blocks.
Just pure SQL statements.

If you cannot generate valid SQL (e.g., insufficient data), return: NO_SQL_POSSIBLE
"""


class DataWriterAgent:
    """Converts document extraction JSON to database INSERTs using Zhipu AI"""
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.zhipu = get_zhipu_client()
    
    def _get_next_id(self, table_name: str, id_column: str) -> int:
        """Get next available ID for a table"""
        try:
            result = self.supabase.table(table_name)\
                .select(id_column)\
                .order(id_column, desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0][id_column] + 1
            return 1
        except:
            return 1
    
    def _find_employee_by_name(self, name: str) -> Optional[int]:
        """Try to find employee_id by name (fuzzy match)"""
        try:
            result = self.supabase.table("employee")\
                .select("employee_id, name")\
                .ilike("name", f"%{name}%")\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["employee_id"]
        except:
            pass
        return None
    
    def generate_sql_from_extraction(
        self,
        extraction_json: Dict[str, Any],
        source_id: int,
        custom_extraction: Optional[str] = None
    ) -> str:
        """
        Use Zhipu AI to generate SQL INSERT statements from extraction JSON
        
        Args:
            extraction_json: Output from document_service.py
            source_id: ID of the source_document record
            custom_extraction: Optional user-requested data to extract
        
        Returns:
            SQL INSERT statements as string
        """
        # Prepare user message with extraction data
        user_message = f"""
Document Extraction Data:
{json.dumps(extraction_json, indent=2)}

Source Document ID: {source_id}
"""
        
        # Add custom extraction request if provided
        if custom_extraction and custom_extraction.strip():
            user_message += f"""

User Custom Extraction Request:
"{custom_extraction}"

IMPORTANT: 
- Analyze if this custom data fits into any existing column
- If YES: use that column
- If NO: this is EXTRA data → write it to the ai_justification column
- Format for ai_justification: "{custom_extraction}: [extracted value from document]"
"""
        
        user_message += """

Generate valid PostgreSQL INSERT statements to write this data to the appropriate table(s).
Replace <SOURCE_ID> placeholder with {source_id}.
""".format(source_id=source_id)
        
        try:
            sql_response = self.zhipu.generate_sql(
                system_prompt=DATABASE_SCHEMA_PROMPT,
                user_message=user_message,
                temperature=0.3  # Low temperature for consistent SQL generation
            )
            
            return sql_response.strip()
        
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def execute_sql_statements(self, sql_statements: str) -> Dict[str, Any]:
        """
        Execute generated SQL statements against Supabase
        
        Args:
            sql_statements: SQL INSERT statements to execute
        
        Returns:
            Execution results with success status
        """
        if not sql_statements or sql_statements == "NO_SQL_POSSIBLE":
            return {
                "success": False,
                "error": "No valid SQL could be generated from extraction data",
                "rows_inserted": 0
            }
        
        # Split multiple statements (one per line)
        statements = [s.strip() for s in sql_statements.split('\n') if s.strip() and not s.strip().startswith('--')]
        
        results = []
        rows_inserted = 0
        
        for statement in statements:
            try:
                # Parse INSERT statement (with or without ON CONFLICT)
                # Format: INSERT INTO table_name (col1, col2, ...) VALUES (val1, val2, ...) [ON CONFLICT ...]
                import re
                
                # Check if this is an UPSERT (has ON CONFLICT)
                has_conflict = 'ON CONFLICT' in statement.upper()
                
                # Extract table name
                table_match = re.search(r'INSERT INTO (\w+)', statement, re.IGNORECASE)
                if not table_match:
                    raise ValueError("Could not parse table name from SQL")
                
                table_name = table_match.group(1)
                
                # Extract columns
                columns_match = re.search(r'\(([^)]+)\)\s*VALUES', statement, re.IGNORECASE)
                if not columns_match:
                    raise ValueError("Could not parse columns from SQL")
                
                columns = [c.strip() for c in columns_match.group(1).split(',')]
                
                # Extract values (stop at ON CONFLICT if present)
                if has_conflict:
                    values_match = re.search(r'VALUES\s*\(([^)]+)\)\s*ON CONFLICT', statement, re.IGNORECASE)
                else:
                    values_match = re.search(r'VALUES\s*\(([^)]+)\)', statement, re.IGNORECASE)
                    
                if not values_match:
                    raise ValueError("Could not parse values from SQL")
                
                values_str = values_match.group(1)
                
                # Parse values (handle strings, numbers, NULL)
                values = []
                current = ""
                in_string = False
                
                for char in values_str:
                    if char == "'" and (not current or current[-1] != '\\'):
                        in_string = not in_string
                    elif char == ',' and not in_string:
                        values.append(current.strip())
                        current = ""
                        continue
                    current += char
                
                if current.strip():
                    values.append(current.strip())
                
                # Convert values to proper types
                parsed_values = []
                for val in values:
                    val = val.strip()
                    if val.upper() == 'NULL':
                        parsed_values.append(None)
                    elif val.startswith("'") and val.endswith("'"):
                        parsed_values.append(val[1:-1])  # String
                    else:
                        try:
                            # Try to parse as number
                            if '.' in val:
                                parsed_values.append(float(val))
                            else:
                                parsed_values.append(int(val))
                        except:
                            parsed_values.append(val)
                
                # Create data dictionary
                data = dict(zip(columns, parsed_values))
                
                # Execute insert or upsert via Supabase
                if has_conflict:
                    # UPSERT: Use Supabase's upsert method
                    result = self.supabase.table(table_name).upsert(data).execute()
                    results.append({
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                        "success": True,
                        "table": table_name,
                        "operation": "upsert"
                    })
                else:
                    # Regular INSERT
                    result = self.supabase.table(table_name).insert(data).execute()
                    results.append({
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                        "success": True,
                        "table": table_name,
                        "operation": "insert"
                    })
                rows_inserted += 1
                
            except Exception as e:
                results.append({
                    "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": rows_inserted > 0,
            "rows_inserted": rows_inserted,
            "total_statements": len(statements),
            "details": results
        }
    
    def process_document_extraction(
        self,
        extraction_json: Dict[str, Any],
        source_id: int,
        custom_extraction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete flow: Generate SQL → Execute → Return results
        
        Args:
            extraction_json: Document extraction from Gemini
            source_id: Source document ID
            custom_extraction: Optional user-requested data to extract
        
        Returns:
            Processing results
        """
        try:
            # Step 1: Generate SQL (with custom extraction if provided)
            sql_statements = self.generate_sql_from_extraction(
                extraction_json, 
                source_id,
                custom_extraction
            )
            
            # Step 2: Execute SQL
            execution_results = self.execute_sql_statements(sql_statements)
            
            return {
                "success": execution_results["success"],
                "source_id": source_id,
                "extraction_summary": {
                    "document_type": extraction_json.get("document_type"),
                    "department": extraction_json.get("department"),
                    "entities_count": len(extraction_json.get("entities", []))
                },
                "sql_generated": sql_statements,
                "execution_results": execution_results
            }
        
        except Exception as e:
            return {
                "success": False,
                "source_id": source_id,
                "error": str(e),
                "extraction_summary": {
                    "document_type": extraction_json.get("document_type"),
                    "department": extraction_json.get("department")
                }
            }


# Singleton instance
_agent = None

def get_data_writer_agent() -> DataWriterAgent:
    """Get or create DataWriterAgent instance"""
    global _agent
    if _agent is None:
        _agent = DataWriterAgent()
    return _agent
