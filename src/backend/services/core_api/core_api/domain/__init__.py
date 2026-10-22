"""The domain: plain Python entities, their rules and the repository ports.

Nothing here knows about HTTP, Pydantic or storage; the DynamoDB adapter in
`core_api.infrastructure.dynamo` implements the ports (ADR 0023).
"""
