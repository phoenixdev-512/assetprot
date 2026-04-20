import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)  # video | image | audio
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    # pending | fingerprinting | fingerprint_partial | protected | failed
    rights_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    territories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="assets")

    # Relationships to models defined in later tasks (AssetFingerprint, Violation, ScanRun).
    # Added here once those models are created so SQLAlchemy can resolve the targets:
    #   fingerprint: Mapped["AssetFingerprint | None"] = relationship("AssetFingerprint", back_populates="asset", uselist=False)
    #   violations: Mapped[list["Violation"]] = relationship("Violation", back_populates="asset")
    #   scan_runs: Mapped[list["ScanRun"]] = relationship("ScanRun", back_populates="asset")
