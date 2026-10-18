-- Fictional demo records; do not use real personal information.
INSERT INTO demo_users(id,display_name,role) VALUES
('22222222-2222-4222-8222-222222222222','Demo Student','STUDENT'),
('33333333-3333-4333-8333-333333333333','Demo Operator','OPERATOR')
ON CONFLICT(id) DO UPDATE SET display_name=EXCLUDED.display_name,role=EXCLUDED.role;
INSERT INTO insurance_invoices(id,student_id,invoice_number,country_code,institution_name,beneficiary_name,fee_type,amount_cny,currency,due_date,source_type,is_real_beneficiary,status)
VALUES('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222',
'DEMO-CN-INS-2026-001','CN','Demo International University (fictional)',
'Demo Student Coverage Center (fictional)','ANNUAL_HEALTH_INSURANCE_PREMIUM',800.00,'CNY',
DATE '2026-11-01','SYNTHETIC',false,'OPEN')
ON CONFLICT(id) DO UPDATE SET amount_cny=EXCLUDED.amount_cny,due_date=EXCLUDED.due_date;
