"""
This module sets up SQLAlchemy relationships after all models are defined
to avoid circular dependencies.
"""

from models.document import Document
from models.organization import Organization
from models.user import User
from models.user_document import UserDocument
from sqlalchemy.orm import relationship


# Set up relationships
def setup_relationships():
    Document.users = relationship(
        "UserDocument", back_populates="document", lazy="joined"
    )
    UserDocument.document = relationship(
        "Document", back_populates="users", lazy="joined"
    )
    UserDocument.user = relationship("User", back_populates="documents")
    User.documents = relationship("UserDocument", back_populates="user")
    User.organization = relationship("Organization", back_populates="users")
    Organization.users = relationship("User", back_populates="organization")
