from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class FamilyLink(Base):
    __tablename__ = "family_links"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    family_member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relation_type = Column(String, nullable=False)  # e.g., "father", "daughter", "partner"
    permission = Column(String, default="read")  # "read", "manage"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="family_members")
    family_member = relationship("User", foreign_keys=[family_member_id], back_populates="linked_to")
