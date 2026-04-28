import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Uuid, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discovered_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="suspected")
    # suspected | confirmed | dismissed | dmca_sent | requires_human_review
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    infringement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # exact_copy | re_encoded | partial_clip | audio_only | false_positive
    transformation_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    estimated_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rights_territory_violation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triage_verdict: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="violations")
    dmca_notices: Mapped[list["DMCANotice"]] = relationship("DMCANotice", back_populates="violation")
