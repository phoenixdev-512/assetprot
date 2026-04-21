from abc import ABC, abstractmethod


class Attestation(ABC):
    @abstractmethod
    async def attest(self, asset_id: str, fingerprint_hash: str) -> str | None:
        """Submit attestation. Returns tx_hash or None if unsupported."""
