from fastapi.exceptions import HTTPException
from sqlalchemy import orm


class Query(orm.Query):
    def get_or_404(self, pk):
        inst = self.get(pk)
        if not inst:
            raise HTTPException(code=404)
        return inst

    def first_or_404(self):
        inst = self.first()
        if not inst:
            raise HTTPException(code=404)
        return inst
