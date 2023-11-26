import json
from typing import TypedDict
import aiohttp

class Atom(TypedDict):
    element: int
    position: list[float, float, float]

Atoms = dict[int, Atom | None]

class Bonds(TypedDict):
    indexes: list[tuple[int, int]]
    values: list[float | None]

class Molecule(TypedDict):
    atoms: Atoms
    bonds: Bonds

CleanedMolecule = tuple[list[Atom], dict[tuple[int, int], float]]

class AddSubstitute(TypedDict):
    atoms: list[Atom]
    bonds_idxs: list[tuple[int, int]]
    bonds_values: list[float]
    current: tuple[int, int]
    target: tuple[int, int]
    class_name: str | None

class Workspace:
    def __init__(self, server: str, name: str) -> None:
        self.__name__ = name
        self.__session__ = aiohttp.ClientSession(f"{server}")

    async def __request__(self, method: str, path: str, **kargs):
        resp = await self.__session__.request(method, f"/workspaces/{self.__name__}{path}", **kargs)
        if resp.ok:
            return resp
        else:
            print(resp.status)
            raise RuntimeError(await resp.text())

    async def create(self, load = None):
        resp = await self.__request__("post", "", data=json.dumps(load), headers = {"Content-Type": "application/json"})
        if not resp.ok:
            raise RuntimeError(await resp.text())

    async def remove(self):
        resp = await self.__request__("delete", "")
        if resp.ok:
            await resp.text()
        else:
            raise RuntimeError(f"Failed to remove target workspace: {await resp.text()}")
        
    async def close(self):
        await self.__session__.close()

    async def export(self):
        return await (await self.__request__("get", "/export")).json()

    async def get_stacks(self) -> list[int]:
        return await (await self.__request__("get", "/stacks")).json()
    
    async def new_stack(self):
        await self.__request__("post", "/stacks")    
    
    async def get_stack(self, stack_idx: int) -> Molecule:
        return await (await self.__request__("get", f"/stacks/{stack_idx}")).json()
    
    async def write_to_layer(self, stack_idx: int, atoms: Atoms, bonds: Bonds) -> bool:
        resp = await self.__request__("patch", f"/stacks/{stack_idx}", json=(atoms, bonds))
        return resp.ok
    
    async def overlay_fill_layer(self, stacks_idxs: list[int]) -> bool:
        resp = await self.__request__("put", f"/stacks/overlay_to", json=[
            {"Fill": {}}, stacks_idxs
        ])
        return resp.ok

    async def remove_stack(self, stack_idx: int) -> bool:
        resp = await self.__request__("delete", f"/stacks/{stack_idx}")
        return resp.ok

    async def is_stack_writable(self, stack_idx: int) -> bool:
        return await (await self.__request__("get", f"/stacks/{stack_idx}/writable")).json()

    async def cleaned_molecule(self, stack_idx: int) -> tuple[list[Atom], dict[tuple[int, int], float]]:
        return await (await self.__request__("get", f"/stacks/{stack_idx}/cleaned")).json()

    async def clone_stack(self, stack_idx: int, amount: int = 1) -> int:
        return await (await self.__request__("post", f"/stacks/{stack_idx}/clone_stack", json={"amount": amount})).json()
    
    async def clone_base(self, stack_idx: int, amount: int = 1) -> int:
        return await (await self.__request__("post", f"/stacks/{stack_idx}/clone_base", json={"amount": amount})).json()

    async def rotation_group(self, stack_idx: int, class_name: str, center: tuple[float, float, float], axis: tuple[float, float, float], angle: float) -> bool:
        resp = await self.__request__("put", f"/stacks/{stack_idx}/rotation/class/{class_name}", data=(center, axis, angle), headers={"Content-Type": "application/json"})
        return resp.ok
    
    async def rotation_group(self, stack_idx: int, class_name: str, vector: [float, float, float]) -> bool:
        resp = await self.__request__("put", f"/stacks/{stack_idx}/translation/class/{class_name}", data=vector, headers={"Content-Type": "application/json"})
        return resp.ok
    
    async def get_neighbors(self, stack_idx: int, atom_idx: int) -> list[tuple[int, float]]:
        resp = await self.__request__("get", f"/stacks/{stack_idx}/atom/{atom_idx}/neighbor")
        return await resp.json()
    
    async def import_structure(self, stack_idx: int, structure: CleanedMolecule) -> bool:
        resp = await self.__request__("post", f"/stacks/{stack_idx}/import", data=structure, headers={"Content-Type": "applcation/json"})
        return resp.ok
    
    async def add_substitute(self, stack_idx: int, add_substitute: AddSubstitute) -> bool:
        resp = await self.__request__("post", f"/stacks/{stack_idx}/substitute", json=add_substitute, headers={"Content-Type": "application/json"})
        return resp.ok
    
    async def get_atom_by_id(self, stack_idx: int, name: str) -> int:
        resp = await self.__request__("get", f"/namespace/id/{name}/stack/{stack_idx}")
        return await resp.json()
    
    async def get_atoms_by_class(self, stack_idx: int, name: str) -> list[int]:
        resp = await self.__request__("get", f"/namespace/class/{name}/stack/{stack_idx}")
        return await resp.json()
    
    async def get_ids(self) -> list[str]:
        resp = await self.__request__("get", f"/namespace/id")
        return await resp.json()
    
    async def set_id(self, atom_idx: int, name: str) -> bool:
        resp = await self.__request__("post", f"/namespace/id", data=(atom_idx, name), headers = {"Content-Type": "application"})
        return resp.ok
    
    async def remove_id_of(self, atom_idx: int) -> bool:
        resp = await self.__request__("delete", f"/namespace/id/atom/{atom_idx}")
        return resp.ok
    
    async def get_id_of(self, atom_idx: int) -> str | None:
        resp = await self.__request__("get", f"/namespace/id/atom/{atom_idx}")
        return await resp.json()
    
    async def get_classes(self) -> list[str]:
        resp = await self.__request__("get", f"/namespace/class")
        return await resp.json()
    
    async def set_classes(self, atoms_idxs: list[int], name: str) -> bool:
        resp = await self.__request__("post", f"/namespace/class", data = (atoms_idxs, name), headers = {"Content-Type": "application/json"})
        return resp.ok
    
    async def remove_atom_from_class(self, atom_idx: int, name: str) -> bool:
        resp = await self.__request__("delete", f"/namespace/class/{name}/atom/{atom_idx}")
        return resp.ok
    
    async def get_atom_classes(self, atom_idx: int) -> list[str]:
        resp = await self.__request__("get", f"/namespace/class/atom/{atom_idx}")
        return await resp.json()
    
    async def remove_atom_from_all_classes(self, atom_idx: int) -> bool:
        resp = await self.__request__("delete", f"/namespace/class/atom/{atom_idx}")
        return resp.ok
    
    async def remove_class(self, name: str) -> bool:
        resp = await self.__request__("delete", f"/namespace/class/{name}")
        return resp.ok