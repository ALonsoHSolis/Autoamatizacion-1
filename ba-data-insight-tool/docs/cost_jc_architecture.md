# Model of Costs Enterprise MVP

## Decision

Model of Costs is implemented incrementally inside the current Streamlit application while keeping a clean boundary between UI, domain, financial engine and repository.

## Current layers

- `src/cost_jc/domain.py`: DTO-like dataclasses for providers, routes, pricing rules, simulations, audit logs and versions.
- `src/cost_jc/engine.py`: central financial formulas and validations.
- `src/cost_jc/repository.py`: session-backed repository for the MVP.
- `src/ui/cost_jc.py`: Streamlit presentation layer.
- `migrations/002_cost_jc_enterprise.sql`: PostgreSQL-oriented DDL for the future API/persistence phase.

## Formula ownership

All financial calculations should stay in `CostJCEngine`:

- Cost IN: provider fixed fee by volume plus provider variable bps.
- Cost OUT: method cost bps plus optional extra cost.
- Revenue: revenue bps plus FX spread revenue.
- Taxes: tax rate over cost base.
- Profit: revenue minus total cost.
- Margin: profit over revenue.
- ROI: profit over total cost.
- Break-even bps: total cost over gross volume.

## Future API contracts

The Streamlit module is ready to move behind API routes such as:

- `GET /cost-jc/providers`
- `GET /cost-jc/routes`
- `POST /cost-jc/routes`
- `POST /cost-jc/simulations`
- `GET /cost-jc/audit-logs`
- `GET /cost-jc/versions`

## Future integrations

Interfaces are represented in the UI but not implemented yet:

- Salesforce pricing requests.
- SAP cost centers and approvals.
- Oracle financial master data.
- Webhooks and REST events.

## Security roadmap

RBAC, authentication, permissions by module and immutable audit logs are planned for a backend phase. The current MVP records audit-like events in session memory only.
