from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents

app = FastAPI(
    title="Document Approval Platform API",
    version="0.1.0",
    description="Multi-tenant document approval platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "doc-approval-platform"}
