"""AI API: everything that talks to language models and retrieval.

Layout (ports and adapters):
- domain/          pure types and the Protocols the use cases depend on
- application/     use cases (PlanTrip, ...) built only on domain ports
- infrastructure/  adapters: model providers, vector store, DynamoDB, HTTP clients
- api/             FastAPI wiring: dependencies, routers, endpoints
"""
