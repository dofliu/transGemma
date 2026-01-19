import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

class HistoryManager:
    def __init__(self, db_path: str = "history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化資料庫表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 建立歷史記錄表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            original_content TEXT,
            translated_content TEXT,
            details TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_history(self, 
                    type: str, 
                    source_lang: str, 
                    target_lang: str, 
                    original_content: str, 
                    translated_content: str, 
                    details: Optional[Dict[str, Any]] = None):
        """
        新增一筆歷史記錄
        
        Args:
            type: 'text', 'image', 'pdf', 'voice', 'video'
            source_lang: 來源語言代碼
            target_lang: 目標語言代碼
            original_content: 原始內容或檔案路徑
            translated_content: 翻譯內容或檔案路徑
            details: 額外資訊 (JSON serializable dict)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        details_json = json.dumps(details, ensure_ascii=False) if details else "{}"
        
        cursor.execute('''
        INSERT INTO history (timestamp, type, source_lang, target_lang, original_content, translated_content, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, type, source_lang, target_lang, original_content, translated_content, details_json))
        
        conn.commit()
        conn.close()
        
    def get_history(self, limit: int = 50, offset: int = 0, type_filter: Optional[str] = None) -> List[Dict]:
        """
        取得歷史記錄
        
        Returns:
            List of dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 讓回傳結果可以用欄位名存取
        cursor = conn.cursor()
        
        query = "SELECT * FROM history"
        params = []
        
        if type_filter:
            query += " WHERE type = ?"
            params.append(type_filter)
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "type": row["type"],
                "source_lang": row["source_lang"],
                "target_lang": row["target_lang"],
                "original_content": row["original_content"],
                "translated_content": row["translated_content"],
                "details": json.loads(row["details"]) if row["details"] else {}
            })
            
        conn.close()
        return results

    def clear_history(self):
        """清空所有歷史記錄"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()

# 單例模式
history_manager = HistoryManager()
