from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Project, Target
from ..schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    TargetConnectionTest,
    TargetCreate,
    TargetRead,
)
from ..services.llm_client import send_chat
from ..services.mcp_client import HTTPMCPClient, StdioMCPClient

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.updated_at.desc())))


@router.post("/projects", response_model=ProjectRead, status_code=201)
async def create_project(body: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    item = Project(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    item = db.get(Project, project_id)
    if not item:
        raise HTTPException(404, "Project not found")
    return item


@router.put("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)
) -> Project:
    item = db.get(Project, project_id)
    if not item:
        raise HTTPException(404, "Project not found")
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: str, db: Session = Depends(get_db)) -> Response:
    item = db.get(Project, project_id)
    if not item:
        raise HTTPException(404, "Project not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/targets", response_model=list[TargetRead])
async def list_targets(
    project_id: str | None = None, db: Session = Depends(get_db)
) -> list[Target]:
    statement = select(Target).order_by(Target.created_at.desc())
    if project_id:
        statement = statement.where(Target.project_id == project_id)
    return list(db.scalars(statement))


@router.post("/targets", response_model=TargetRead, status_code=201)
async def create_target(body: TargetCreate, db: Session = Depends(get_db)) -> Target:
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "Project not found")
    item = Target(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/targets/{target_id}", response_model=TargetRead)
async def update_target(
    target_id: str, body: TargetCreate, db: Session = Depends(get_db)
) -> Target:
    item = db.get(Target, target_id)
    if not item:
        raise HTTPException(404, "Target not found")
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "Project not found")
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/targets/{target_id}", status_code=204)
async def delete_target(target_id: str, db: Session = Depends(get_db)) -> Response:
    item = db.get(Target, target_id)
    if not item:
        raise HTTPException(404, "Target not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.post("/targets/{target_id}/test")
async def test_target_connection(
    target_id: str, body: TargetConnectionTest, db: Session = Depends(get_db)
) -> dict[str, object]:
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    if not body.confirm_active_request:
        raise HTTPException(
            409, "The connection test sends a real request and requires confirmation"
        )
    settings = get_settings()
    if target.target_type == "mcp_http":
        http_client = HTTPMCPClient(
            target.endpoint or "",
            dict(target.configuration.get("headers", {})),
            settings,
            target.remote_authorized,
        )
        discovery = await http_client.discover()
        return {
            "connected": True,
            "protocol": "mcp",
            "server_info": discovery.server_info,
            "capabilities": discovery.capabilities,
            "tools": len(discovery.tools),
            "suggested_configuration": {},
        }
    if target.target_type == "mcp_stdio":
        async with StdioMCPClient(
            str(target.configuration.get("command", "")),
            list(target.configuration.get("args", [])),
            settings,
        ) as stdio_client:
            discovery = await stdio_client.discover()
        return {
            "connected": True,
            "protocol": "mcp-stdio",
            "server_info": discovery.server_info,
            "capabilities": discovery.capabilities,
            "tools": len(discovery.tools),
            "suggested_configuration": {},
        }
    if target.target_type == "rag":
        raise HTTPException(422, "RAG targets do not expose a standard chat connection test")
    result = await send_chat(
        target,
        [{"role": "user", "content": body.test_message}],
        100,
        settings,
    )
    suggested = {
        "response_format": result.metadata.get("protocol", "json"),
    }
    if result.metadata.get("response_path") and not target.configuration.get("response_path"):
        suggested["response_path"] = result.metadata["response_path"]
    return {
        "connected": True,
        "protocol": result.metadata.get("protocol"),
        "model": result.metadata.get("model"),
        "response": result.text,
        "tool_calls": result.tool_calls,
        "events": result.events,
        "completed": result.completed,
        "metadata": result.metadata,
        "suggested_configuration": suggested,
    }
