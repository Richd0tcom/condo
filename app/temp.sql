    
    
    op.execute(
        "ALTER TABLE tenant ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on tenants \
            USING (id = current_setting('app.current_tenant'));",
    )

    op.execute(
        "ALTER TABLE every_other_table ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on toys \
            USING (tenant_id = current_setting('app.current_tenant'));",
    )