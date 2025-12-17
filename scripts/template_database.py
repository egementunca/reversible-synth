#!/usr/bin/env python3
"""
SQLite database for identity template storage with deduplication.

Provides thread-safe and process-safe operations for cluster usage.
"""

import hashlib
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import sys

script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir.parent))

from reversible_synth.gates import CustomGate, Circuit


# Thread-local storage for connections
_local = threading.local()


def get_default_db_path() -> Path:
    """Get the default database path."""
    return Path(__file__).parent.parent / "data" / "templates.db"


class TemplateDatabase:
    """
    SQLite database for storing identity templates with deduplication.
    
    Features:
    - Hash-based deduplication
    - Process-safe with WAL mode
    - Efficient batch inserts
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(_local, 'connections'):
            _local.connections = {}
        
        db_key = str(self.db_path)
        if db_key not in _local.connections:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=60.0,  # Wait up to 60s for locks
                isolation_level=None  # Auto-commit for WAL
            )
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            _local.connections[db_key] = conn
        
        return _local.connections[db_key]
    
    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                width INTEGER NOT NULL,
                depth INTEGER NOT NULL,
                gate_count INTEGER NOT NULL,
                gates_json TEXT NOT NULL,
                canonical_hash TEXT UNIQUE NOT NULL,
                hardness_score REAL,
                is_verified INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                job_id TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_width_depth 
                ON templates(width, depth);
            CREATE INDEX IF NOT EXISTS idx_hash 
                ON templates(canonical_hash);
            CREATE INDEX IF NOT EXISTS idx_width 
                ON templates(width);
        """)
    
    @staticmethod
    def compute_hash(circuit: Circuit) -> str:
        """
        Compute canonical hash for deduplication.
        
        Uses a canonical representation of the gate sequence.
        """
        # Sort gates by a canonical ordering for hash
        gate_tuples = [(g.target, g.control1, g.control2) for g in circuit.gates]
        canonical = json.dumps({
            'width': circuit.n_bits,
            'gates': gate_tuples
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]
    
    def add_template(self, circuit: Circuit, hardness_score: float = 0.0,
                     job_id: str = None) -> Tuple[bool, Optional[int]]:
        """
        Add a template to the database.
        
        Args:
            circuit: The identity circuit to add
            hardness_score: Pre-computed hardness score
            job_id: Identifier of the generating job
        
        Returns:
            (success, id) - success is False if duplicate
        """
        conn = self._get_connection()
        
        gates_json = json.dumps([
            {'t': g.target, 'c1': g.control1, 'c2': g.control2}
            for g in circuit.gates
        ])
        canonical_hash = self.compute_hash(circuit)
        
        try:
            cursor = conn.execute("""
                INSERT INTO templates 
                    (width, depth, gate_count, gates_json, canonical_hash, 
                     hardness_score, job_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                circuit.n_bits,
                len(circuit),  # depth = gate count for sequential
                len(circuit),
                gates_json,
                canonical_hash,
                hardness_score,
                job_id
            ))
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate hash
            return False, None
    
    def add_templates_batch(self, circuits: List[Tuple[Circuit, float]],
                            job_id: str = None) -> Tuple[int, int]:
        """
        Add multiple templates in a batch.
        
        Args:
            circuits: List of (circuit, hardness_score) tuples
            job_id: Identifier of the generating job
        
        Returns:
            (added_count, duplicate_count)
        """
        added = 0
        duplicates = 0
        
        conn = self._get_connection()
        conn.execute("BEGIN")
        
        try:
            for circuit, score in circuits:
                success, _ = self.add_template(circuit, score, job_id)
                if success:
                    added += 1
                else:
                    duplicates += 1
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        
        return added, duplicates
    
    def get_template(self, template_id: int) -> Optional[Circuit]:
        """Get a template by ID."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT width, gates_json FROM templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        if row is None:
            return None
        
        return self._row_to_circuit(row)
    
    def get_templates(self, width: int = None, depth: int = None,
                      limit: int = None) -> List[Circuit]:
        """
        Query templates with optional filters.
        
        Args:
            width: Filter by circuit width
            depth: Filter by circuit depth
            limit: Maximum number to return
        
        Returns:
            List of Circuit objects
        """
        conn = self._get_connection()
        
        query = "SELECT width, gates_json FROM templates WHERE 1=1"
        params = []
        
        if width is not None:
            query += " AND width = ?"
            params.append(width)
        if depth is not None:
            query += " AND depth = ?"
            params.append(depth)
        
        query += " ORDER BY hardness_score DESC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        return [self._row_to_circuit(row) for row in rows]
    
    def _row_to_circuit(self, row: sqlite3.Row) -> Circuit:
        """Convert a database row to a Circuit object."""
        width = row['width']
        gates_data = json.loads(row['gates_json'])
        gates = [
            CustomGate(g['t'], g['c1'], g['c2'], width)
            for g in gates_data
        ]
        return Circuit(width, gates)
    
    def count_by_width_depth(self) -> Dict[Tuple[int, int], int]:
        """Get counts grouped by (width, depth)."""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT width, depth, COUNT(*) as count
            FROM templates
            GROUP BY width, depth
            ORDER BY width, depth
        """).fetchall()
        
        return {(row['width'], row['depth']): row['count'] for row in rows}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self._get_connection()
        
        total = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
        by_width = dict(conn.execute("""
            SELECT width, COUNT(*) FROM templates GROUP BY width
        """).fetchall())
        
        return {
            'total_templates': total,
            'by_width': by_width,
            'db_path': str(self.db_path),
            'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
    
    def exists(self, circuit: Circuit) -> bool:
        """Check if a circuit already exists in the database."""
        conn = self._get_connection()
        canonical_hash = self.compute_hash(circuit)
        row = conn.execute(
            "SELECT 1 FROM templates WHERE canonical_hash = ?",
            (canonical_hash,)
        ).fetchone()
        return row is not None


def main():
    """Test the database."""
    from reversible_synth.identity_synthesis import NonTrivialIdentityGenerator
    
    print("=== Template Database Test ===")
    
    db = TemplateDatabase()
    print(f"Database: {db.db_path}")
    
    # Generate some test templates
    gen = NonTrivialIdentityGenerator(3)
    
    added = 0
    dups = 0
    for i in range(10):
        circuit = gen.generate_fast(target_length=6, max_attempts=100)
        if circuit:
            score = gen.hardness_score(circuit)
            success, tid = db.add_template(circuit, score, job_id="test")
            if success:
                added += 1
                print(f"  Added template {tid}: {len(circuit)} gates, score={score:.1f}")
            else:
                dups += 1
    
    print(f"\nAdded: {added}, Duplicates: {dups}")
    print(f"\nStats: {db.get_stats()}")


if __name__ == "__main__":
    main()
