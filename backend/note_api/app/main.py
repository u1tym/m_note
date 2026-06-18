from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from note_api.app.config import get_settings
from note_api.app.routers import files, folders, items, parts, tables

settings = get_settings()

app = FastAPI(title="Note API", version="1.0.0")

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(items.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(parts.router)
app.include_router(tables.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
