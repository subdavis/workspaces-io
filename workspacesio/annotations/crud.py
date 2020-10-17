from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from workspacesio.common import schemas, indexing_schemas

from . import models as indexing_models


def annotation_dataset_create(
    db: Session, user: schemas.UserDB, args: indexing_schemas.AnnotationDatasetCreate
):
    pass


def annotation_dataset_list(db: Session, user: schemas.UserDB):
    pass
