from fastapi import FastAPI

app = FastAPI(
    title="Document Approval Platform API",
    version="0.1.0",
    description="Multi-tenant document approval platform.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Liveness probe. Always returns 200 when the app is up."""
    return {"status": "ok", "service": "doc-approval-platform"}