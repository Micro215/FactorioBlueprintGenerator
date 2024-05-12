import copy


class Creator():
    def __init__(self, entity_base: dict, connection_base: dict, neighbours_base: dict) -> None:
        self.entity_base = entity_base
        self.connection_base = connection_base
        self.neighbours_base = neighbours_base

    def EntityCreate(self, entity_counter: int, name: str, x: int, y: int) -> dict:
        entity = copy.deepcopy(self.entity_base)

        entity["entity_number"] = entity_counter
            
        entity["name"] = name
        entity["position"] = {"x": x, "y": y}

        return entity
    
    def ConnectionCreate(self, entity: dict) -> None:
        connect = copy.deepcopy(self.connection_base)
        entity.update(connect)
        
    def ConnectionAdd(self, entity: dict, connect_id: int, number: str, color: str, circuit_id: int = None) -> None:

        if circuit_id is None:
            entity["connections"][number][color].append({"entity_id": connect_id})

        else:
            entity["connections"][number][color].append({"entity_id": connect_id, "circuit_id": circuit_id})

    def NeighboursConnect(self, entity: dict, neighbours_list: list) -> None:
        neighbours = copy.deepcopy(self.neighbours_base)

        for i in neighbours_list:
            neighbours["neighbours"].append(i)

        entity.update(neighbours)