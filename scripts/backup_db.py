import asyncio
import sys
import json
import gzip
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.db.models.university import University
from app.db.models.faculty import Faculty
from app.db.models.program import Program
from app.db.models.user import User
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def backup_table(db: AsyncSession, model_class, table_name: str):
    """Backup a single table"""
    logger.info(f"Backing up {table_name}...")
    
    result = await db.execute(select(model_class))
    records = result.scalars().all()
    
    backup_data = []
    for record in records:
        # Convert to dict, handling special types
        record_dict = {}
        for column in model_class.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            record_dict[column.name] = value
        backup_data.append(record_dict)
    
    logger.info(f"Backed up {len(backup_data)} records from {table_name}")
    return backup_data

async def create_backup():
    """Create a complete database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_file = backup_dir / f"backup_{timestamp}.json.gz"
    
    logger.info(f"Creating backup: {backup_file}")
    
    backup_data = {
        "timestamp": timestamp,
        "version": "1.0.0",
        "tables": {}
    }
    
    async with AsyncSessionLocal() as db:
        # Backup each table
        tables_to_backup = [
            (University, "universities"),
            (Faculty, "faculty"),
            (Program, "programs"),
            (User, "users")
        ]
        
        for model_class, table_name in tables_to_backup:
            backup_data["tables"][table_name] = await backup_table(db, model_class, table_name)
    
    # Write compressed backup
    with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, default=str)
    
    logger.info(f"Backup created successfully: {backup_file}")
    return backup_file

if __name__ == "__main__":
    asyncio.run(create_backup())