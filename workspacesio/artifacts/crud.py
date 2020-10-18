from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from workspacesio.common import schemas

from . import models as artifact_models
