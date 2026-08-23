from sqlalchemy import Column, Integer, String, Float, DateTime, Index
import datetime
from backend.app.database.timescale_engine import Base, engine
from sqlalchemy import text

class TickData(Base):
    """
    Model for storing live ticks into TimescaleDB.
    """
    __tablename__ = "tick_data"

    # We use a composite primary key (id, time) because TimescaleDB requires 
    # the partitioning column (time) to be part of the primary key.
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, primary_key=True, index=True)
    symbol = Column(String, index=True)
    source = Column(String) # mt5 or ctrader
    
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

# Index for fast retrieval by symbol and time
Index('idx_symbol_time', TickData.symbol, TickData.time.desc())

def init_hypertable():
    """
    Convert the regular PostgreSQL table into a TimescaleDB hypertable.
    """
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    with engine.begin() as conn:
        # Check if it's already a hypertable
        result = conn.execute(text("SELECT count(*) FROM _timescaledb_catalog.hypertable WHERE table_name = 'tick_data'"))
        count = result.scalar()
        if count == 0:
            conn.execute(text("SELECT create_hypertable('tick_data', 'time');"))
            print("Successfully converted tick_data into a TimescaleDB hypertable.")
