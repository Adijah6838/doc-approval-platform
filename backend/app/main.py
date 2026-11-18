from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents

app = FastAPI(
    title="Document Approval Platform API",
    version="0.1.0",
    description="Multi-tenant document approval platform.",
)

# Allow the React frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # The Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "doc-approval-platform"}