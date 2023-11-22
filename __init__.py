from typing import TypedDict
import aiohttp

class Atom(TypedDict):
    element: int
    position: list[float, float, float]

type Atoms = dict[int, Atom | None]

class Bonds(TypedDict):
    indexes: list[tuple[int, int]]
    values: list[float | None]

class Molecule(TypedDict):
    atoms: Atoms
    bonds: Bonds

type CleanedMolecule = tuple[list[Atom], dict[tuple[int, int], float]]

class AddSubstitute(TypedDict):
    atoms: list[Atom]
    bond: dict[tuple[int, int], float]
    current: tuple[int, int]
    target: tuple[int, int]
    class_name: str | None

class Workspace:
    def __init__(self, server: str, name: str) -> None:
        self.__name__ = name
        self.__session__ = aiohttp.ClientSession(f"{server}")

    def __request__(self, method: str, path: str, **kargs):
        return self.__session__.request(method, f"/workspaces/{self.__name__}{path}", **kargs)

    async def create(self):
        resp = await self.__request__("post", "", data="null", headers = {"Content-Type": "application/json"})
        if not resp.ok:
            raise RuntimeError(await resp.text())

    async def remove(self):
        resp = await self.__request__("delete", "")
        if resp.ok:
            content = await resp.text()
            await self.__session__.close()
        else:
            raise RuntimeError(f"Failed to remove target workspace: {await resp.text()}")

    async def export(self):
        return await (await self.__request__("get", "/export")).json()

    async def get_stacks(self) -> list[int]:
        return await (await self.__request__("get", "/stacks")).json()
    
    async def new_stack(self):
        await self.__request__("post", "/stacks")    
    
    async def get_stack(self, stack_id: int) -> Molecule:
        return await (await self.__request__("get", f"/stacks/{stack_id}")).json()
    
    async def write_to_layer(self, stack_id: int, atoms: Atoms, bonds: Bonds) -> bool:
        resp = await self.__request__("patch", f"/stacks/{stack_id}", json=(atoms, bonds))
        return resp.ok
    
    async def overlay_fill_layer(self, stack_id: int) -> bool:
        resp = await self.__request__("put", f"/stacks/{stack_id}", json={
            "Fill": {}
        })
        return resp.ok

    async def remove_stack(self, stack_id: int) -> bool:
        resp = await self.__request__("delete", f"/stacks/{stack_id}")
        return resp.ok

    async def is_stack_writable(self, stack_id: int) -> bool:
        return await (await self.__request__("get", f"/stacks/{stack_id}/writable")).json()

    async def cleaned_molecule(self, stack_id: int) -> tuple[list[Atom], dict[tuple[int, int], float]]:
        return await (await self.__request__("get", f"/stacks/{stack_id}/cleaned")).json()

    async def clone_stack(self, stack_id: int) -> int:
        return await (await self.__request__("post", f"/stacks/{stack_id}/clone_stack")).json()
    
    async def clone_base(self, stack_id: int) -> int:
        return await (await self.__request__("post", f"/stacks/{stack_id}/clone_base")).json()

    async def rotation_group(self, stack_id: int, class_name: str, center: tuple[float, float, float], axis: tuple[float, float, float], angle: float) -> bool:
        resp = await self.__request__("put", f"/stacks/{stack_id}/rotation/class/{class_name}", data=(center, axis, angle), headers={"Content-Type": "application/json"})
        return resp.ok
    
    async def rotation_group(self, stack_id: int, class_name: str, vector: [float, float, float]) -> bool:
        resp = await self.__request__("put", f"/stacks/{stack_id}/translation/class/{class_name}", data=vector, headers={"Content-Type": "application/json"})
        return resp.ok
    
    async def get_neighbors(self, stack_id: int, atom_id: int) -> list[tuple[int, float]]:
        resp = await self.__request__("get", f"/stacks/{stack_id}/atom/{atom_id}/neighbor")
        return await resp.json()
    
    async def import_structure(self, stack_id: int, structure: CleanedMolecule) -> bool:
        resp = await self.__request__("post", f"/stacks/{stack_id}/import", data=structure, headers={"Content-Type": "applcation/json"})
        return resp.ok
    
    async def add_substitute(self, stack_id: int, add_substitute: AddSubstitute) -> bool:
        resp = await self.__request__("post", f"/stacks/{stack_id}/subsitute", data=add_substitute, headers={"Content-Type": "application/json"})
        return resp.ok