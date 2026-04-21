from blockchain.protocol import Attestation


class NullAttestation(Attestation):
    async def attest(self, asset_id: str, fingerprint_hash: str) -> str | None:
        return None
