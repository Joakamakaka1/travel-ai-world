"""What both Bedrock adapters need: a client's configuration and what a
failure means.

The chat provider and the embedder talk to different Bedrock APIs but face the
same service: the same credential chain (the function's role in AWS, the SSO
session on a laptop), the same transient errors, and the same decision about
whether another attempt is worth making.
"""

from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

# Transient on Bedrock's side: worth another attempt.
RETRYABLE_ERROR_CODES = frozenset(
    {
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
        "ModelNotReadyException",
        "ModelTimeoutException",
    }
)

_RETRYABLE_CONNECTION_ERRORS = (
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
    ConnectionClosedError,
)


def client_config(
    *,
    region: str,
    connect_timeout: float,
    read_timeout: float,
    max_pool_connections: int = 10,
) -> Config:
    """botocore settings for a Bedrock client.

    Retries are ours (`RetryPolicy`), so botocore's are switched off: one
    attempt per call, and the adapter decides what to do with a failure.
    `max_pool_connections` has to cover however many calls an adapter keeps in
    flight, or botocore drops and reopens connections under the surplus.
    """
    return Config(
        region_name=region,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={"mode": "standard", "total_max_attempts": 1},
        max_pool_connections=max_pool_connections,
    )


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, ClientError):
        return error_code(exc) in RETRYABLE_ERROR_CODES
    return isinstance(exc, _RETRYABLE_CONNECTION_ERRORS)


def error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", ""))
