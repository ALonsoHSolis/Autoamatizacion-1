CREATE TABLE IF NOT EXISTS cost_jc_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    method TEXT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    fixed_fee NUMERIC(18,4) NOT NULL DEFAULT 0,
    variable_bps NUMERIC(18,4) NOT NULL DEFAULT 0,
    sla_hours INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_routes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    origin_country TEXT NOT NULL,
    destination_country TEXT NOT NULL,
    method TEXT NOT NULL,
    provider_id TEXT NOT NULL REFERENCES cost_jc_providers(id),
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    approval_version TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_pricing_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    route_id TEXT NOT NULL REFERENCES cost_jc_routes(id),
    revenue_bps NUMERIC(18,4) NOT NULL DEFAULT 0,
    spread_bps NUMERIC(18,4) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(9,4) NOT NULL DEFAULT 0,
    min_margin_pct NUMERIC(9,4) NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_simulations (
    id BIGSERIAL PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES cost_jc_routes(id),
    provider_id TEXT NOT NULL REFERENCES cost_jc_providers(id),
    amount NUMERIC(18,4) NOT NULL,
    volume INTEGER NOT NULL,
    fx_rate NUMERIC(18,8) NOT NULL,
    cost_in NUMERIC(18,4) NOT NULL,
    cost_out NUMERIC(18,4) NOT NULL,
    fx_spread_revenue NUMERIC(18,4) NOT NULL,
    taxes NUMERIC(18,4) NOT NULL,
    total_cost NUMERIC(18,4) NOT NULL,
    revenue NUMERIC(18,4) NOT NULL,
    profit NUMERIC(18,4) NOT NULL,
    margin_pct NUMERIC(9,4) NOT NULL,
    roi_pct NUMERIC(9,4) NOT NULL,
    break_even_bps NUMERIC(18,4) NOT NULL,
    validations JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_by TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    detail TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_versions (
    id TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    label TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cost_jc_roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_cost_jc_routes_provider ON cost_jc_routes(provider_id);
CREATE INDEX IF NOT EXISTS ix_cost_jc_simulations_route_created ON cost_jc_simulations(route_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_cost_jc_audit_entity_created ON cost_jc_audit_logs(entity, created_at DESC);
