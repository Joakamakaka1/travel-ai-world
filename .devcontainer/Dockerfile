FROM mcr.microsoft.com/devcontainers/base:ubuntu

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Node.js (matches CI)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# uv (Python package manager), Python 3.12 managed by uv (matches CI), and just (task runner)
USER vscode
ENV PATH="/home/vscode/.local/bin:${PATH}" \
    UV_PYTHON=3.12
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv python install 3.12 \
    && curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "$HOME/.local/bin"
