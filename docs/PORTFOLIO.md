# AI Business Automation Hub — portfolio description

## Short description

AI Business Automation Hub is a local customer inquiry operations platform built
with FastAPI, PostgreSQL, and Vue 3. It combines a validated intake API, stored
classification insights, real operational metrics, and a controlled inquiry lifecycle
in a responsive dashboard. Docker Compose provides isolated application and n8n
databases plus an Ollama service for future workflow integration.

## Project case study

Customer inquiries often arrive as unstructured text, making it difficult to see
which conversations need attention and where they stand. This project gives an
operator one workspace to search, filter, prioritize, inspect, resolve, and reopen
inquiries while retaining the original customer message.

The Python backend uses Pydantic contracts, SQLAlchemy sessions, and Alembic
migrations. Server-side queries provide pagination, literal text search, semantic
priority sorting, and full-database aggregates. Status updates follow a defined
state machine and use a conditional update to reject stale writes. The intake API
remains compatible with clients that do not provide classification fields.

The Vue 3 and TypeScript frontend uses Vue Router, Pinia, and a typed API client.
It includes a responsive dark interface, bookmarkable inquiry views, accessible
detail dialogs, keyboard navigation, and explicit pending/success/error feedback.
AI Insights shows only stored evidence and identifies unclassified records; it
never invents confidence scores or claims verified model provenance.

The target automation architecture is Webhook → n8n → Ollama → FastAPI → PostgreSQL
→ HubSpot → Email Alerts. This repository implements the management API, storage,
dashboard, and local infrastructure. External automation, CRM sync, and email
delivery need a separate workflow and are not claimed as completed integrations.
There is no public deployment or simulated authentication.

## Engineering highlights

- Preserved existing intake clients, migration history, and persistent data.
- Added constrained status progression, reopening, and stale-state protection.
- Derived metrics from database queries rather than sample data.
- Separated application/automation databases and kept published services on localhost.
- Added backend, frontend, browser, and PostgreSQL-specific checks, isolating test
  writes from existing records.
- Documented reproducible setup, implementation boundaries, and production needs.

Use the README demo with synthetic data. Show metrics, filtering, AI Insights,
status progression, and reopening; present the target integration diagram separately.
Link VERIFICATION.md for checks actually executed. Do not claim accuracy, performance
improvements, CRM delivery, or alerts without measured evidence.
