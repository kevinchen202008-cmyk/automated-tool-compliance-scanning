"""
数据库迁移脚本：将评分字段改为可空
Migration script: Make score fields nullable
"""

import sqlite3
from pathlib import Path
import sys

def migrate_database(db_path: str):
    """
    迁移数据库：将compliance_reports表的评分字段改为可空
    
    SQLite不支持直接ALTER COLUMN，需要：
    1. 创建新表（带新结构）
    2. 复制数据
    3. 删除旧表
    4. 重命名新表
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compliance_reports'")
        if not cursor.fetchone():
            print("表 compliance_reports 不存在，无需迁移")
            return
        
        print("开始迁移数据库...")
        
        # 1. 创建新表（带可空字段）
        # 注意：references 是SQLite保留字，需要用方括号括起来
        cursor.execute("""
            CREATE TABLE compliance_reports_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id INTEGER NOT NULL,
                score_overall REAL,
                score_security REAL,
                score_license REAL,
                score_maintenance REAL,
                score_performance REAL,
                score_tos REAL,
                is_compliant BOOLEAN,
                reasons TEXT,
                recommendations TEXT,
                [references] TEXT,
                tos_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            )
        """)
        
        # 2. 复制数据（保留现有数据）
        cursor.execute("""
            INSERT INTO compliance_reports_new 
            (id, tool_id, score_overall, score_security, score_license, 
             score_maintenance, score_performance, score_tos, is_compliant,
             reasons, recommendations, [references], tos_analysis, created_at, updated_at)
            SELECT 
                id, tool_id, score_overall, score_security, score_license,
                score_maintenance, score_performance, score_tos, is_compliant,
                reasons, recommendations, [references], tos_analysis, created_at, updated_at
            FROM compliance_reports
        """)
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE compliance_reports")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE compliance_reports_new RENAME TO compliance_reports")
        
        # 5. 重新创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_compliance_reports_tool_id ON compliance_reports(tool_id)")
        
        conn.commit()
        print("[OK] 数据库迁移成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 数据库迁移失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # 从配置文件获取数据库路径
    try:
        from src.config import get_config
        config = get_config()
        db_path = config.database.path
    except:
        # 默认路径
        db_path = "data/compliance.db"
    
    if not Path(db_path).exists():
        print(f"数据库文件不存在: {db_path}")
        print("首次运行，无需迁移")
        sys.exit(0)
    
    print(f"数据库路径: {db_path}")
    migrate_database(db_path)
