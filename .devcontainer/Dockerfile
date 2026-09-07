FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Optional agent CLIs (npm packages) installed next to Claude Code. Override
# from the host before opening the container, e.g.
#   DEVCONTAINER_EXTRA_AGENT_CLIS="@openai/codex" code .
# Set it to the empty string to install none.
ARG EXTRA_AGENT_CLIS="@openai/codex @google/gemini-cli @github/copilot"

# System dependencies. ripgrep / fd / jq are what coding agents shell out to.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    postgresql-client \
    ripgrep \
    fd-find \
    jq \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# GitHub CLI (agents use it for PRs, issues and CI status)
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
         -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
         > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Node.js (matches CI)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Optional agent CLIs (see EXTRA_AGENT_CLIS above)
RUN if [ -n "$EXTRA_AGENT_CLIS" ]; then npm install -g $EXTRA_AGENT_CLIS; fi

# Shell history survives rebuilds (named volume, see docker-compose.yml)
RUN mkdir -p /commandhistory && chown vscode:vscode /commandhistory

# Per-user tools: uv + Python 3.12 (matches CI), just, Claude Code (native
# installer: self-updating, no npm). CLAUDE_CONFIG_DIR keeps every Claude Code
# file (settings, credentials, ~/.claude.json) inside one volume-backed folder.
USER vscode
ENV PATH="/home/vscode/.local/bin:${PATH}" \
    UV_PYTHON=3.12 \
    CLAUDE_CONFIG_DIR=/home/vscode/.claude
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv python install 3.12 \
    && curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to "$HOME/.local/bin" \
    && curl -fsSL https://claude.ai/install.sh | bash \
    # Agent config dirs must exist, owned by vscode, so the named volumes
    # mounted on them inherit that ownership.
    && mkdir -p "$HOME/.claude" "$HOME/.codex" "$HOME/.gemini" "$HOME/.copilot" \
    && echo 'export HISTFILE=/commandhistory/.bash_history' >> "$HOME/.bashrc" \
    && echo 'export HISTFILE=/commandhistory/.zsh_history' >> "$HOME/.zshrc"
