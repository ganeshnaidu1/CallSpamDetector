"""
Call Repository
Database operations for storing and retrieving call records and analysis results
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class CallRepository:
    """SQLite database repository for call records"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.DATABASE_PATH
        self.connection = None
        
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            # Ensure database directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize database in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._init_db_sync)
            
            logger.info(f"Database initialized at {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _init_db_sync(self):
        """Initialize database synchronously"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Call records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                phone_number TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration REAL,
                transcription TEXT,
                audio_features TEXT,
                conversation_analysis TEXT,
                combined_risk_score REAL,
                is_suspicious BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis results table for detailed breakdowns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                risk_score REAL,
                confidence REAL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (call_id) REFERENCES call_records (call_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_call_records_call_id ON call_records (call_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_call_records_start_time ON call_records (start_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_call_records_risk_score ON call_records (combined_risk_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_call_id ON analysis_results (call_id)')
        
        self.connection.commit()
    
    async def save_call_record(self, call_data: Dict[str, Any]) -> bool:
        """Save a complete call record"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._save_call_record_sync, call_data)
        except Exception as e:
            logger.error(f"Error saving call record: {e}")
            return False
    
    def _save_call_record_sync(self, call_data: Dict[str, Any]) -> bool:
        """Save call record synchronously"""
        try:
            cursor = self.connection.cursor()
            
            # Prepare data
            call_id = call_data.get('call_id')
            phone_number = call_data.get('phone_number')
            start_time = call_data.get('start_time')
            end_time = call_data.get('end_time')
            duration = call_data.get('duration', 0)
            transcription = call_data.get('transcription', '')
            audio_features = json.dumps(call_data.get('audio_features', {}))
            conversation_analysis = json.dumps(call_data.get('conversation_analysis', {}))
            combined_risk_score = call_data.get('combined_risk_score', 0.0)
            is_suspicious = call_data.get('is_suspicious', False)
            
            # Insert or update call record
            cursor.execute('''
                INSERT OR REPLACE INTO call_records 
                (call_id, phone_number, start_time, end_time, duration, transcription, 
                 audio_features, conversation_analysis, combined_risk_score, is_suspicious, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (call_id, phone_number, start_time, end_time, duration, transcription,
                  audio_features, conversation_analysis, combined_risk_score, is_suspicious))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error in _save_call_record_sync: {e}")
            return False
    
    async def save_analysis_result(self, call_id: str, analysis_type: str, 
                                 risk_score: float, confidence: float, 
                                 details: Dict[str, Any]) -> bool:
        """Save individual analysis result"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._save_analysis_result_sync,
                call_id, analysis_type, risk_score, confidence, details
            )
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return False
    
    def _save_analysis_result_sync(self, call_id: str, analysis_type: str,
                                 risk_score: float, confidence: float,
                                 details: Dict[str, Any]) -> bool:
        """Save analysis result synchronously"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_results 
                (call_id, analysis_type, timestamp, risk_score, confidence, details)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
            ''', (call_id, analysis_type, risk_score, confidence, json.dumps(details)))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error in _save_analysis_result_sync: {e}")
            return False
    
    async def get_call_record(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific call record"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_call_record_sync, call_id)
        except Exception as e:
            logger.error(f"Error getting call record: {e}")
            return None
    
    def _get_call_record_sync(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call record synchronously"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM call_records WHERE call_id = ?', (call_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error in _get_call_record_sync: {e}")
            return None
    
    async def get_recent_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call records"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_recent_calls_sync, limit)
        except Exception as e:
            logger.error(f"Error getting recent calls: {e}")
            return []
    
    def _get_recent_calls_sync(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent calls synchronously"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM call_records 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error in _get_recent_calls_sync: {e}")
            return []
    
    async def get_suspicious_calls(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get suspicious calls from the last N days"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_suspicious_calls_sync, days)
        except Exception as e:
            logger.error(f"Error getting suspicious calls: {e}")
            return []
    
    def _get_suspicious_calls_sync(self, days: int) -> List[Dict[str, Any]]:
        """Get suspicious calls synchronously"""
        try:
            cursor = self.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM call_records 
                WHERE is_suspicious = 1 AND start_time >= ?
                ORDER BY combined_risk_score DESC, start_time DESC
            ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error in _get_suspicious_calls_sync: {e}")
            return []
    
    async def get_call_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get call statistics for the last N days"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_call_statistics_sync, days)
        except Exception as e:
            logger.error(f"Error getting call statistics: {e}")
            return {}
    
    def _get_call_statistics_sync(self, days: int) -> Dict[str, Any]:
        """Get call statistics synchronously"""
        try:
            cursor = self.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Total calls
            cursor.execute('SELECT COUNT(*) FROM call_records WHERE start_time >= ?', (cutoff_date,))
            total_calls = cursor.fetchone()[0]
            
            # Suspicious calls
            cursor.execute('SELECT COUNT(*) FROM call_records WHERE is_suspicious = 1 AND start_time >= ?', (cutoff_date,))
            suspicious_calls = cursor.fetchone()[0]
            
            # Average risk score
            cursor.execute('SELECT AVG(combined_risk_score) FROM call_records WHERE start_time >= ?', (cutoff_date,))
            avg_risk_score = cursor.fetchone()[0] or 0.0
            
            # High risk calls (>0.7)
            cursor.execute('SELECT COUNT(*) FROM call_records WHERE combined_risk_score > 0.7 AND start_time >= ?', (cutoff_date,))
            high_risk_calls = cursor.fetchone()[0]
            
            # Average call duration
            cursor.execute('SELECT AVG(duration) FROM call_records WHERE duration > 0 AND start_time >= ?', (cutoff_date,))
            avg_duration = cursor.fetchone()[0] or 0.0
            
            return {
                'total_calls': total_calls,
                'suspicious_calls': suspicious_calls,
                'high_risk_calls': high_risk_calls,
                'avg_risk_score': round(avg_risk_score, 3),
                'avg_duration': round(avg_duration, 2),
                'suspicious_rate': round((suspicious_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error in _get_call_statistics_sync: {e}")
            return {}
    
    async def cleanup_old_records(self, days: int = 90) -> int:
        """Clean up old call records"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._cleanup_old_records_sync, days)
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    def _cleanup_old_records_sync(self, days: int) -> int:
        """Clean up old records synchronously"""
        try:
            cursor = self.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete old analysis results first (foreign key constraint)
            cursor.execute('DELETE FROM analysis_results WHERE created_at < ?', (cutoff_date,))
            analysis_deleted = cursor.rowcount
            
            # Delete old call records
            cursor.execute('DELETE FROM call_records WHERE created_at < ?', (cutoff_date,))
            records_deleted = cursor.rowcount
            
            self.connection.commit()
            
            total_deleted = analysis_deleted + records_deleted
            if total_deleted > 0:
                logger.info(f"Cleaned up {records_deleted} call records and {analysis_deleted} analysis results older than {days} days")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error in _cleanup_old_records_sync: {e}")
            return 0
    
    async def close(self):
        """Close database connection"""
        try:
            if self.connection:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.close)
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            if self.connection:
                self.connection.close()
        except:
            pass
