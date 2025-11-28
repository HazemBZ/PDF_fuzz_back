# An example of using standalone Python builds with multistage images.

# First, build the application in the `/app` directory
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.12

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Then, use a final image that contains the `uv` runtime
FROM ghcr.io/astral-sh/uv:bookworm-slim

# Configure where managed python lives (must match builder)
ENV UV_PYTHON_INSTALL_DIR=/python

# Install utility tools
# TODOD: cleanup packages not needed and add poppler before removing apt lists
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libmagic-dev
   
RUN apt-get install -y poppler-utils
RUN rm -rf /var/lib/apt/lists/*

# Setup a non-root user
# RUN groupadd --system --gid 999 nonroot \
#  && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the managed Python directory from the builder
# COPY --from=builder --chown=nonroot:nonroot /python $UV_PYTHON_INSTALL_DIR
COPY --from=builder /python $UV_PYTHON_INSTALL_DIR

# Copy the application from the builder
# COPY --from=builder --chown=nonroot:nonroot /app /app
COPY --from=builder /app /app

# Copy the virtualenv out of /app into the non-root user's home so host bind-mounting /app
# won't overwrite the image venv and cause permission issues.
# COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Use the non-root user to run our application
# USER nonroot

# Use `/app` as the working directory
WORKDIR /app

# Copy entrypoint and make executable
# COPY --chown=nonroot:nonroot entrypoint.sh setup.sh /
COPY entrypoint.sh setup.sh /
RUN chmod +x /entrypoint.sh /setup.sh

# Allow switching behaviour via build arg
ARG IS_BACKEND
ENV IS_BACKEND=$IS_BACKEND

# Default entrypoint remains the script (can call uv there or rely on CMD below)
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

# Run Django using uv so it runs inside the managed Python environment.
# uv run -- <command...> ensures the command runs with the uv-managed interpreter/env.
CMD ["uv", "run", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]