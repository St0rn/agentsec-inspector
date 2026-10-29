from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Connector, Project, Target
from ..schemas import ConnectorCreate
from ..security import SecretStore

router = APIRouter(tags=["connectors"])


def _public(item: Connector) -> dict[str, object]:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "target_id": item.target_id,
        "name": item.name,
        "connector_type": item.connector_type,
        "configuration": item.configuration,
        "has_secret": bool(item.encrypted_secret),
        "enabled": item.enabled,
        "last_status": item.last_status,
    }


@router.get("/connectors")
async def list_connectors(
    project_id: str | None = None, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    statement = select(Connector).order_by(Connector.name)
    if project_id:
        statement = statement.where(Connector.project_id == project_id)
    return [_public(item) for item in db.scalars(statement)]


@router.post("/connectors", status_code=201)
async def create_connector(
    body: ConnectorCreate, db: Session = Depends(get_db)
) -> dict[str, object]:
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "Project not found")
    if body.target_id:
        target = db.get(Target, body.target_id)
        if not target or target.project_id != body.project_id:
            raise HTTPException(404, "Target not found in project")
    item = Connector(
        project_id=body.project_id,
        target_id=body.target_id,
        name=body.name,
        connector_type=body.connector_type,
        configuration=body.configuration,
        encrypted_secret=SecretStore(get_settings().data_dir).encrypt(body.secret)
        if body.secret
        else None,
        enabled=body.enabled,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _public(item)


@router.delete("/connectors/{connector_id}", status_code=204)
async def delete_connector(connector_id: str, db: Session = Depends(get_db)) -> Response:
    item = db.get(Connector, connector_id)
    if not item:
        raise HTTPException(404, "Connector not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
