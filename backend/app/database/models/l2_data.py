from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.database.timescale_engine import Base, engine
from sqlalchemy import text

class L2SnapshotData(Base):
    """
    Model for storing Live L2 Snapshots (Market Book) into TimescaleDB using JSONB.
    """
    __tablename__ = "l2_snapshot_data"

    # Composite primary key for TimescaleDB (id + partitioning time column)
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, primary_key=True, index=True)
    symbol = Column(String, index=True)
    source = Column(String) # mt5 or ctrader
    
    # Store bids and asks arrays efficiently in Postgres JSONB
    bids = Column(JSONB, nullable=False)
    asks = Column(JSONB, nullable=False)

# Index for fast retrieval
Index('idx_l2_symbol_time', L2SnapshotData.symbol, L2SnapshotData.time.desc())

def init_l2_hypertable():
    """
    Convert the table into a TimescaleDB hypertable.
    """
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        # Check if it's already a hypertable
        result = conn.execute(text("SELECT count(*) FROM _timescaledb_catalog.hypertable WHERE table_name = 'l2_snapshot_data'"))
        count = result.scalar()
        if count == 0:
            conn.execute(text("SELECT create_hypertable('l2_snapshot_data', 'time');"))
            print("Successfully converted l2_snapshot_data into a TimescaleDB hypertable.")
