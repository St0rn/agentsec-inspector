from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Target
from ..schemas import ProjectCreate, ProjectRead, ProjectUpdate, TargetCreate, TargetRead

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
