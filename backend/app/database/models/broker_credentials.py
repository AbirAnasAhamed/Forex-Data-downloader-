from sqlalchemy import Column, Integer, String, Enum
import enum
from backend.app.database.timescale_engine import Base
from backend.app.core.security.encryption import encryption_service

class EngineType(enum.Enum):
    MT5 = "mt5"
    CTRADER = "ctrader"

class BrokerCredential(Base):
    __tablename__ = "broker_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # In a real app, foreign key to User table
    engine_type = Column(Enum(EngineType), nullable=False)
    
    # MT5 specific
    server_name = Column(String, nullable=True)
    login_id = Column(String, nullable=True)
    
    # cTrader specific
    ctid = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    
    # Encrypted fields (used by both, depending on engine)
    _encrypted_password = Column("encrypted_password", String, nullable=True)
    _encrypted_secret = Column("encrypted_secret", String, nullable=True)
    _encrypted_token = Column("encrypted_token", String, nullable=True)

    @property
    def password(self):
        return encryption_service.decrypt(self._encrypted_password)

    @password.setter
    def password(self, plain_text):
        self._encrypted_password = encryption_service.encrypt(plain_text)

    @property
    def secret(self):
        return encryption_service.decrypt(self._encrypted_secret)

    @secret.setter
    def secret(self, plain_text):
        self._encrypted_secret = encryption_service.encrypt(plain_text)

    @property
    def token(self):
        return encryption_service.decrypt(self._encrypted_token)

    @token.setter
    def token(self, plain_text):
        self._encrypted_token = encryption_service.encrypt(plain_text)
