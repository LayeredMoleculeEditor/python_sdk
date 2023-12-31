from typing import Any, Optional, Tuple, List, Dict
import aiohttp
from pydantic import BaseModel

JSON_REQUEST_HEADER = {"Content-Type": "application/json"}


class Atom(BaseModel):
    element: int
    position: Tuple[float, float, float]


Atoms = Dict[int, Atom | None]


class Bonds(BaseModel):
    indexes: List[Tuple[int, int]]
    values: List[float | None]


class Molecule(BaseModel):
    atoms: Atoms
    bonds: Bonds


class CleanedMolecule(BaseModel):
    atoms: List[Atom]
    bonds_idxs: List[Tuple[int, int]]
    bonds_values: List[float]


class AddSubstitute(BaseModel):
    structure: CleanedMolecule
    current: Tuple[int, int]
    target: Tuple[int, int]
    class_name: str

class CloneResult(BaseModel):
    value: Tuple[int, int]

    @property
    def start(self) -> int:
        self.value[0]

    @property
    def end(self) -> int:
        self.value[1]

class Workspace:
    def __init__(self, server: str, name: str) -> None:
        self.__name__ = name
        self.__session__ = aiohttp.ClientSession(server)

    async def __request__(self, method: str, path: str, **kargs: Any):
        resp = await self.__session__.request(
            method, f"/ws/{self.__name__}{path}", **kargs
        )
        if resp.ok:
            return resp
        else:
            print(resp.status)
            raise RuntimeError(await resp.text())

    async def create(self, load: Optional[str] = None):
        resp = await self.__request__(
            "post", "", data=load, headers=JSON_REQUEST_HEADER
        )
        if not resp.ok:
            raise RuntimeError(await resp.text())

    async def remove(self):
        resp = await self.__request__("delete", "")
        if resp.ok:
            await resp.text()
        else:
            raise RuntimeError(
                f"Failed to remove target workspace: {await resp.text()}"
            )

    async def close(self):
        await self.__session__.close()

    async def export(self) -> str:
        resp = await self.__request__("get", "/export")
        return await resp.text()

    async def get_stacks(self) -> List[int]:
        resp = await self.__request__("get", "/stacks")
        return await resp.json()

    async def new_stack(self) -> None:
        await self.__request__("post", "/stacks")

    async def get_stack(self, stack_idx: int) -> Molecule:
        resp = await self.__request__("get", f"/stacks/{stack_idx}")
        data = await resp.text()
        return Molecule.model_validate_json(data)

    async def write_to_layer(self, stack_idx: int, molecule: Molecule) -> None:
        await self.__request__(
            "patch",
            f"/stacks/{stack_idx}",
            data=molecule.model_dump_json,
            headers=JSON_REQUEST_HEADER,
        )

    async def overlay_fill_layer(self, stacks_idxs: List[int]) -> None:
        await self.__request__(
            "put", f"/stacks/overlay_to", json=[{"Fill": {}}, stacks_idxs]
        )

    async def overlay_layer(self, stacks_idxs: List[int], layer: Any) -> None:
        await self.__request__("put", f"/stacks/overlay_to", json=[layer, stacks_idxs])

    async def remove_stack(self, stack_idx: int):
        await self.__request__("delete", f"/stacks/{stack_idx}")

    async def is_stack_writable(self, stack_idx: int) -> bool:
        resp = await self.__request__("get", f"/stacks/{stack_idx}/writable")
        return await resp.json()

    async def cleaned_molecule(
        self, stack_idx: int
    ) -> CleanedMolecule:
        resp = await self.__request__("get", f"/stacks/{stack_idx}/cleaned")
        data = await resp.text()
        return CleanedMolecule.model_validate_json(data)

    async def clone_stack(self, stack_idx: int, amount: int = 1) -> CloneResult:
        resp = await self.__request__(
            "post", f"/stacks/{stack_idx}/clone_stack", json={"amount": amount}
        )
        data = await resp.text()
        return CloneResult.model_validate_json(data)

    async def clone_base(self, stack_idx: int, amount: int = 1) -> CloneResult:
        resp = await self.__request__(
            "post", f"/stacks/{stack_idx}/clone_base", json={"amount": amount}
        )
        data = await resp.text()
        return CloneResult.model_validate_json(data)

    async def rotation_group(
        self,
        stack_idx: int,
        class_name: str,
        center: Tuple[float, float, float],
        axis: Tuple[float, float, float],
        angle: float,
    ):
        await self.__request__(
            "put",
            f"/stacks/{stack_idx}/rotation/class/{class_name}",
            data=(center, axis, angle),
            headers={"Content-Type": "application/json"},
        )

    async def translation_group(
        self, stack_idx: int, class_name: str, vector: Tuple[float, float, float]
    ):
        await self.__request__(
            "put",
            f"/stacks/{stack_idx}/translation/class/{class_name}",
            data=vector,
            headers={"Content-Type": "application/json"},
        )

    async def get_neighbors(
        self, stack_idx: int, atom_idx: int
    ) -> List[Tuple[int, float]]:
        resp = await self.__request__(
            "get", f"/stacks/{stack_idx}/atom/{atom_idx}/neighbor"
        )
        return await resp.json()

    async def import_structure(
        self, stack_idx: int, structure: CleanedMolecule, name: str
    ) -> bool:
        resp = await self.__request__(
            "post",
            f"/stacks/{stack_idx}/import/{name}",
            json=structure,
            headers={"Content-Type": "application/json"},
        )
        return resp.ok

    async def add_substitute(
        self, stack_idx: int, add_substitute: AddSubstitute
    ) -> bool:
        resp = await self.__request__(
            "post",
            f"/stacks/{stack_idx}/substitute",
            json=add_substitute,
            headers={"Content-Type": "application/json"},
        )
        return resp.ok

    async def get_atom_by_id(self, stack_idx: int, name: str) -> int:
        resp = await self.__request__("get", f"/namespace/id/{name}/stack/{stack_idx}")
        return await resp.json()

    async def get_atoms_by_class(self, stack_idx: int, name: str) -> List[int]:
        resp = await self.__request__(
            "get", f"/namespace/class/{name}/stack/{stack_idx}"
        )
        return await resp.json()

    async def get_ids(self) -> List[str]:
        resp = await self.__request__("get", f"/namespace/id")
        return await resp.json()

    async def set_id(self, atom_idx: int, name: str) -> bool:
        resp = await self.__request__(
            "post",
            f"/namespace/id",
            data=(atom_idx, name),
            headers={"Content-Type": "application"},
        )
        return resp.ok

    async def remove_id_of(self, atom_idx: int) -> bool:
        resp = await self.__request__("delete", f"/namespace/id/atom/{atom_idx}")
        return resp.ok

    async def get_id_of(self, atom_idx: int) -> str | None:
        resp = await self.__request__("get", f"/namespace/id/atom/{atom_idx}")
        return await resp.json()

    async def get_classes(self) -> List[str]:
        resp = await self.__request__("get", f"/namespace/class")
        return await resp.json()

    async def set_classes(self, atoms_idxs: List[int], name: str) -> bool:
        resp = await self.__request__(
            "post",
            f"/namespace/class",
            data=(atoms_idxs, name),
            headers={"Content-Type": "application/json"},
        )
        return resp.ok

    async def remove_atom_from_class(self, atom_idx: int, name: str) -> bool:
        resp = await self.__request__(
            "delete", f"/namespace/class/{name}/atom/{atom_idx}"
        )
        return resp.ok

    async def get_atom_classes(self, atom_idx: int) -> List[str]:
        resp = await self.__request__("get", f"/namespace/class/atom/{atom_idx}")
        return await resp.json()

    async def remove_atom_from_all_classes(self, atom_idx: int) -> bool:
        resp = await self.__request__("delete", f"/namespace/class/atom/{atom_idx}")
        return resp.ok

    async def remove_class(self, name: str) -> bool:
        resp = await self.__request__("delete", f"/namespace/class/{name}")
        return resp.ok
