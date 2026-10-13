# idn-econ-mcp — MCP server (stdio) dengan data ekonomi Indonesia sudah tertanam.
# Data ikut di dalam image supaya pemakai tidak perlu membangun basis data sendiri.
FROM python:3.11-slim

WORKDIR /app

# Label wajib: registry MCP resmi menolak image OCI tanpa anotasi ini.
LABEL io.modelcontextprotocol.server.name="io.github.anYoneo/idn-econ"

# SDK MCP 2.x (menyediakan mcp.server.MCPServer)
RUN pip install --no-cache-dir "mcp>=2.0.0,<3"

COPY src/server.py /app/server.py
COPY data/vpsrevenue.db /app/data/vpsrevenue.db

ENV IDN_ECON_DB=/app/data/vpsrevenue.db
ENV PYTHONUNBUFFERED=1

# Transport stdio: klien MCP menjalankan container ini dan berbicara lewat stdin/stdout.
ENTRYPOINT ["python", "/app/server.py"]
