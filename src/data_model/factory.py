from pydantic import BaseModel
import config

class Factory(BaseModel):
    id: int
    name: str
    is_depot: bool | None = None
    location: tuple[float, float] | None = None


    def __str__(self):
        return f"Factory(id={self.id}, name={self.name},)"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Factory):
            return False
        return self.id == other.id and self.name == other.name and self.is_depot == other.is_depot

    def __hash__(self):
        return hash((self.id, self.name, self.is_depot))
    
def create_depot_factory() -> Factory:
    return Factory(id=config.DEPOT_ID, name=f"City_{config.DEPOT_ID}", is_depot=True)