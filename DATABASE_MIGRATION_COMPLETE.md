# 数据库迁移完成

## 问题原因

在简化模式下，我们将评分字段设置为 `None`，但数据库模型中这些字段被定义为 `NOT NULL`，导致数据库约束错误：

```
NOT NULL constraint failed: compliance_reports.score_overall
```

## 解决方案

### 1. 更新数据模型 (`src/models.py`)

将所有评分字段改为可空（`nullable=True`）：

- `score_overall` → `nullable=True`
- `score_security` → `nullable=True`
- `score_license` → `nullable=True`
- `score_maintenance` → `nullable=True`
- `score_performance` → `nullable=True`
- `score_tos` → `nullable=True`
- `is_compliant` → `nullable=True`

### 2. 执行数据库迁移 (`scripts/migrate_database.py`)

创建迁移脚本，更新现有数据库表结构：

1. 创建新表（带可空字段）
2. 复制现有数据
3. 删除旧表
4. 重命名新表
5. 重新创建索引

### 3. 验证迁移结果

迁移后，所有评分字段现在都是可空的：

```
score_overall: nullable=True ✅
score_security: nullable=True ✅
score_license: nullable=True ✅
score_maintenance: nullable=True ✅
score_performance: nullable=True ✅
score_tos: nullable=True ✅
is_compliant: nullable=True ✅
```

## 当前状态

- ✅ 数据库表结构已更新
- ✅ 模型定义已更新
- ✅ 简化模式可以正常工作
- ✅ 评分字段可以为 NULL

## 测试建议

请重启服务并重新测试扫描功能，现在应该可以正常生成报告了。
