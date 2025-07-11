"""Initial migration

Revision ID: 80b8196606cc
Revises: 
Create Date: 2025-07-01 19:45:18.135782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '80b8196606cc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('conflict_resolutions',
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('internal_id', sa.String(length=255), nullable=True),
    sa.Column('external_id', sa.String(length=255), nullable=False),
    sa.Column('internal_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('external_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('resolution_strategy', sa.String(length=50), nullable=True),
    sa.Column('resolved_by', sa.UUID(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    # isolation policy
    op.execute(
        "ALTER TABLE conflict_resolutions ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on conflict_resolutions \
            USING ( \
        current_setting('app.is_super_admin', true) = 'true' \
        OR id = current_setting('app.current_org')::uuid\
    );",
    )


    op.create_index(op.f('ix_conflict_resolutions_id'), 'conflict_resolutions', ['id'], unique=False)
    op.create_index(op.f('ix_conflict_resolutions_organization_id'), 'conflict_resolutions', ['organization_id'], unique=False)
    op.create_table('data_sync_logs',
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('records_processed', sa.Integer(), nullable=True),
    sa.Column('records_synced', sa.Integer(), nullable=True),
    sa.Column('records_failed', sa.Integer(), nullable=True),
    sa.Column('conflicts_detected', sa.Integer(), nullable=True),
    sa.Column('conflicts_resolved', sa.Integer(), nullable=True),
    sa.Column('execution_time', sa.Float(), nullable=True),
    sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_sync_logs_id'), 'data_sync_logs', ['id'], unique=False)
    op.create_index(op.f('ix_data_sync_logs_organization_id'), 'data_sync_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_data_sync_logs_service_name'), 'data_sync_logs', ['service_name'], unique=False)
    op.create_table('external_services',
    sa.Column('slug', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('webhook_url', sa.String(), nullable=False),
    sa.Column('api_base_url', sa.String(), nullable=False),
    sa.Column('auth_type', sa.String(), nullable=False),
    sa.Column('secret_key', sa.String(), nullable=False),
    sa.Column('retry_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('event_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rate_limit', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('slug', 'id')
    )
    op.create_index(op.f('ix_external_services_id'), 'external_services', ['id'], unique=False)
    op.create_index(op.f('ix_external_services_slug'), 'external_services', ['slug'], unique=False)
    op.create_table('integration_health',
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('response_time_ms', sa.Float(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_health_id'), 'integration_health', ['id'], unique=False)
    op.create_index(op.f('ix_integration_health_service_name'), 'integration_health', ['service_name'], unique=False)
    op.create_table('organizations',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('subscription_tier', sa.String(length=50), nullable=True),
    sa.Column('employee_limit', sa.Integer(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute(
        "ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on organizations \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR id = current_setting('app.current_org')::uuid\
    );",
    )



    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_table('processed_events',
    sa.Column('event_hash', sa.String(length=64), nullable=False),
    sa.Column('event_id', sa.String(length=255), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processed_events_event_hash'), 'processed_events', ['event_hash'], unique=True)
    op.create_index(op.f('ix_processed_events_id'), 'processed_events', ['id'], unique=False)
    op.create_table('sync_configurations',
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('direction', sa.String(length=20), nullable=False),
    sa.Column('frequency', sa.String(length=20), nullable=False),
    sa.Column('conflict_strategy', sa.String(length=50), nullable=False),
    sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_sync_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    #isolation policy
    op.execute(
        "ALTER TABLE sync_configurations ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on sync_configurations \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR id = current_setting('app.current_org')::uuid\
    );",
    )



    op.create_index(op.f('ix_sync_configurations_id'), 'sync_configurations', ['id'], unique=False)
    op.create_index(op.f('ix_sync_configurations_organization_id'), 'sync_configurations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sync_configurations_service_name'), 'sync_configurations', ['service_name'], unique=False)
    op.create_table('sync_status',
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('service_name', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('progress_percentage', sa.Integer(), nullable=True),
    sa.Column('records_processed', sa.Integer(), nullable=True),
    sa.Column('records_remaining', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


    #isolation policy
    op.execute(
        "ALTER TABLE sync_status ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on sync_status \
            USING ( \
        current_setting('app.is_super_admin', true) = 'true' \
        OR id = current_setting('app.current_org')::uuid \
    );",
    )


    op.create_index(op.f('ix_sync_status_id'), 'sync_status', ['id'], unique=False)
    op.create_index(op.f('ix_sync_status_organization_id'), 'sync_status', ['organization_id'], unique=False)
    op.create_index(op.f('ix_sync_status_service_name'), 'sync_status', ['service_name'], unique=False)
    op.create_table('tenants',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('domain', sa.String(length=255), nullable=True),
    sa.Column('plan_type', sa.String(length=50), nullable=True),
    sa.Column('employee_count', sa.Integer(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('domain', name='uq_tenant_domain'),
    sa.UniqueConstraint('slug', name='uq_tenant_slug')
    )

    op.execute(
        "ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on tenants \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR id = current_setting('app.current_tenant')::uuid\
    );",
    )



    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)
    op.create_table('vendors',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)
    op.create_index(op.f('ix_vendors_name'), 'vendors', ['name'], unique=True)
    op.create_table('webhook_events',
    sa.Column('service_name', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=True),
    sa.Column('idempotency_key', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('last_attempted_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_events_id'), 'webhook_events', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_events_idempotency_key'), 'webhook_events', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_webhook_events_service_name'), 'webhook_events', ['service_name'], unique=False)
    op.create_index(op.f('ix_webhook_events_status'), 'webhook_events', ['status'], unique=False)
    op.create_index(op.f('ix_webhook_events_tenant_id'), 'webhook_events', ['tenant_id'], unique=False)
    op.create_table('workflow_templates',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('estimated_duration_in_minutes', sa.Integer(), nullable=True),
    sa.Column('requires_approval', sa.Boolean(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_templates_id'), 'workflow_templates', ['id'], unique=False)
    op.create_table('employee_provisioning',
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('personal_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('role_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('access_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('equipment_needs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    #isolation policy
    op.execute(
        "ALTER TABLE employee_provisioning ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on employee_provisioning \
            USING ( \
        current_setting('app.is_super_admin', true) = 'true' \
        OR id = current_setting('app.current_org')::uuid \
    );",
    )



    op.create_index(op.f('ix_employee_provisioning_id'), 'employee_provisioning', ['id'], unique=False)
    op.create_table('organization_integrations',
    sa.Column('integration_type', sa.String(length=255), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('last_sync', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    #isolation policy
    op.execute(
        "ALTER TABLE organization_integrations ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on organization_integrations \
            USING ( \
        current_setting('app.is_super_admin', true) = 'true' \
        OR id = current_setting('app.current_org')::uuid \
    );",
    )



    op.create_index(op.f('ix_organization_integrations_id'), 'organization_integrations', ['id'], unique=False)
    op.create_table('organization_settings',
    sa.Column('features_enabled', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('webhook_endpoints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', name='uq_org_settings')
    )

    #isolation policy
    op.execute(
        "ALTER TABLE organization_settings ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY org_isolation on organization_settings \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR id = current_setting('app.current_org')::uuid \
    );",
    )




    op.create_index(op.f('ix_organization_settings_id'), 'organization_settings', ['id'], unique=False)
    op.create_table('organization_tenants',
    sa.Column('tenant_id', sa.UUID(), nullable=True),
    sa.Column('organization_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'tenant_id', name='uq_org_tenant')
    )
    op.create_index(op.f('ix_organization_tenants_id'), 'organization_tenants', ['id'], unique=False)
    op.create_table('tenant_sso_config',
    sa.Column('tenant_id', sa.UUID(), nullable=True),
    sa.Column('provider', sa.String(length=255), nullable=False),
    sa.Column('provider_tenant_id', sa.UUID(), nullable=True),
    sa.Column('client_id', sa.String(), nullable=False),
    sa.Column('domain', sa.String(length=255), nullable=False),
    sa.Column('attribute_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('role_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )



        # isolation policy
    op.execute(
        "ALTER TABLE tenant_sso_config ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on tenant_sso_config \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR tenant_id = current_setting('app.current_tenant')::uuid\
    );",
    )




    op.create_index(op.f('ix_tenant_sso_config_id'), 'tenant_sso_config', ['id'], unique=False)
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=255), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant')
    )


    # isolation policy
    op.execute(
        "ALTER TABLE users ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on users \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR tenant_id = current_setting('app.current_tenant')::uuid\
    );",
    )



    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('vendor_events',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('vendor_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_events_id'), 'vendor_events', ['id'], unique=False)
    op.create_index(op.f('ix_vendor_events_name'), 'vendor_events', ['name'], unique=False)
    op.create_table('audit_logs',
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('resource_type', sa.String(length=100), nullable=False),
    sa.Column('resource_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('user_email', sa.String(length=255), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('endpoint', sa.String(length=255), nullable=True),
    sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )



    #isolation policy
    op.execute(
        "ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;",
    )
    op.execute(
        "CREATE POLICY tenant_isolation on audit_logs \
            USING (\
        current_setting('app.is_super_admin', true) = 'true'\
        OR tenant_id = current_setting('app.current_tenant')::uuid\
    );",
    )



    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
    op.create_table('user_auth_scheme',
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('auth_type', sa.String(length=255), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('is_locked', sa.Boolean(), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('last_login', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_auth_scheme_id'), 'user_auth_scheme', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_auth_scheme_id'), table_name='user_auth_scheme')
    op.drop_table('user_auth_scheme')
    op.drop_index(op.f('ix_audit_logs_tenant_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_vendor_events_name'), table_name='vendor_events')
    op.drop_index(op.f('ix_vendor_events_id'), table_name='vendor_events')
    op.drop_table('vendor_events')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_tenant_sso_config_id'), table_name='tenant_sso_config')
    op.drop_table('tenant_sso_config')
    op.drop_index(op.f('ix_organization_tenants_id'), table_name='organization_tenants')
    op.drop_table('organization_tenants')
    op.drop_index(op.f('ix_organization_settings_id'), table_name='organization_settings')
    op.drop_table('organization_settings')
    op.drop_index(op.f('ix_organization_integrations_id'), table_name='organization_integrations')
    op.drop_table('organization_integrations')
    op.drop_index(op.f('ix_employee_provisioning_id'), table_name='employee_provisioning')
    op.drop_table('employee_provisioning')
    op.drop_index(op.f('ix_workflow_templates_id'), table_name='workflow_templates')
    op.drop_table('workflow_templates')
    op.drop_index(op.f('ix_webhook_events_tenant_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_status'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_service_name'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_idempotency_key'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_table('webhook_events')
    op.drop_index(op.f('ix_vendors_name'), table_name='vendors')
    op.drop_index(op.f('ix_vendors_id'), table_name='vendors')
    op.drop_table('vendors')
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_id'), table_name='tenants')
    op.drop_table('tenants')
    op.drop_index(op.f('ix_sync_status_service_name'), table_name='sync_status')
    op.drop_index(op.f('ix_sync_status_organization_id'), table_name='sync_status')
    op.drop_index(op.f('ix_sync_status_id'), table_name='sync_status')
    op.drop_table('sync_status')
    op.drop_index(op.f('ix_sync_configurations_service_name'), table_name='sync_configurations')
    op.drop_index(op.f('ix_sync_configurations_organization_id'), table_name='sync_configurations')
    op.drop_index(op.f('ix_sync_configurations_id'), table_name='sync_configurations')
    op.drop_table('sync_configurations')
    op.drop_index(op.f('ix_processed_events_id'), table_name='processed_events')
    op.drop_index(op.f('ix_processed_events_event_hash'), table_name='processed_events')
    op.drop_table('processed_events')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
    op.drop_index(op.f('ix_integration_health_service_name'), table_name='integration_health')
    op.drop_index(op.f('ix_integration_health_id'), table_name='integration_health')
    op.drop_table('integration_health')
    op.drop_index(op.f('ix_external_services_slug'), table_name='external_services')
    op.drop_index(op.f('ix_external_services_id'), table_name='external_services')
    op.drop_table('external_services')
    op.drop_index(op.f('ix_data_sync_logs_service_name'), table_name='data_sync_logs')
    op.drop_index(op.f('ix_data_sync_logs_organization_id'), table_name='data_sync_logs')
    op.drop_index(op.f('ix_data_sync_logs_id'), table_name='data_sync_logs')
    op.drop_table('data_sync_logs')
    op.drop_index(op.f('ix_conflict_resolutions_organization_id'), table_name='conflict_resolutions')
    op.drop_index(op.f('ix_conflict_resolutions_id'), table_name='conflict_resolutions')
    op.drop_table('conflict_resolutions')
    # ### end Alembic commands ###
