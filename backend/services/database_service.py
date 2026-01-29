"""
Database Service - PostgreSQL backend for audit trail.

Provides persistent storage for audit logs, media assets, and conversation audits.
Supports connection pooling, async operations, and automatic retries.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import asyncpg

from config import DATABASE_URL, DATABASE_ENABLED
from models import AuditLog, AuditEventType, MediaAsset, ConversationAudit

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    PostgreSQL backend for audit data storage.

    Features:
    - Connection pooling for efficient concurrent access
    - Async operations for non-blocking database calls
    - Automatic JSON serialization for complex fields
    - Fallback to in-memory when database is not available
    """

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._enabled = DATABASE_ENABLED
        self._initialized = False

        # In-memory fallback when database is not available
        self._memory_logs: Dict[str, AuditLog] = {}
        self._memory_media: Dict[str, MediaAsset] = {}
        self._memory_conversations: Dict[str, ConversationAudit] = {}

    async def initialize(self):
        """Initialize database connection pool."""
        if not self._enabled:
            logger.info("Database not enabled, using in-memory storage for audit logs")
            self._initialized = True
            return

        if self._initialized:
            return

        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=20,
                command_timeout=30,
            )
            self._initialized = True
            logger.info("Database service initialized for audit trail")
        except Exception as e:
            logger.warning(
                f"Failed to initialize database: {e}, using in-memory storage"
            )
            self._enabled = False
            self._initialized = True

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    def is_enabled(self) -> bool:
        """Check if database storage is enabled."""
        return self._enabled and self.pool is not None

    # ========================================================================
    # AUDIT LOG METHODS
    # ========================================================================

    async def store_audit_log(self, log: AuditLog) -> str:
        """
        Store audit log in database.

        Args:
            log: The audit log entry to store

        Returns:
            The log ID
        """
        if not self.is_enabled():
            # Fallback to in-memory
            self._memory_logs[log.id] = log
            return log.id

        query = """
            INSERT INTO audit_logs (
                id, timestamp, event_type, user_id, session_id, ip_address,
                user_agent, resource_type, resource_id, details, status,
                error_message, thread_id, post_id, agent_run_id,
                correlation_id, request_id, response_time_ms
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            ON CONFLICT (id) DO UPDATE SET
                timestamp = EXCLUDED.timestamp,
                event_type = EXCLUDED.event_type,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                details = EXCLUDED.details
            RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    query,
                    log.id,
                    log.timestamp,
                    log.event_type.value,
                    log.user_id,
                    log.session_id,
                    log.ip_address,
                    log.user_agent,
                    log.resource_type,
                    log.resource_id,
                    json.dumps(log.details),
                    log.status,
                    log.error_message,
                    log.thread_id,
                    log.post_id,
                    log.agent_run_id,
                    log.details.get("correlation_id"),
                    log.details.get("request_id"),
                    log.details.get("response_time_ms"),
                )
                return result["id"]
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")
            # Fallback to in-memory
            self._memory_logs[log.id] = log
            return log.id

    async def query_audit_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Query audit logs with filters and pagination.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            thread_id: Filter by thread ID
            status: Filter by status
            start_date: Filter events after this date
            end_date: Filter events before this date
            search_query: Search in details JSON
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Dict with logs list and pagination info
        """
        # If database not enabled, use in-memory
        if not self.is_enabled():
            return self._query_memory_logs(
                event_type=event_type,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                thread_id=thread_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size,
            )

        # Build query dynamically
        conditions = []
        params = []
        param_count = 0

        if event_type:
            param_count += 1
            conditions.append(f"event_type = ${param_count}")
            params.append(event_type)

        if user_id:
            param_count += 1
            conditions.append(f"user_id = ${param_count}::uuid")
            params.append(user_id)

        if resource_type:
            param_count += 1
            conditions.append(f"resource_type = ${param_count}")
            params.append(resource_type)

        if resource_id:
            param_count += 1
            conditions.append(f"resource_id = ${param_count}::uuid")
            params.append(resource_id)

        if thread_id:
            param_count += 1
            conditions.append(f"thread_id = ${param_count}::uuid")
            params.append(thread_id)

        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)

        if start_date:
            param_count += 1
            conditions.append(f"timestamp >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            conditions.append(f"timestamp <= ${param_count}")
            params.append(end_date)

        if search_query:
            param_count += 1
            conditions.append(f"details::text ILIKE ${param_count}")
            params.append(f"%{search_query}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            async with self.pool.acquire() as conn:
                # Get total count
                count_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"
                total = await conn.fetchval(count_query, *params)

                # Get paginated results
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT * FROM audit_logs
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ${param_count + 1} OFFSET ${param_count + 2}
                """
                params.extend([page_size, offset])

                rows = await conn.fetch(data_query, *params)

                # Convert rows to AuditLog objects
                logs = []
                for row in rows:
                    logs.append(
                        AuditLog(
                            id=str(row["id"]),
                            timestamp=row["timestamp"],
                            event_type=AuditEventType(row["event_type"]),
                            user_id=str(row["user_id"]) if row["user_id"] else None,
                            session_id=str(row["session_id"])
                            if row["session_id"]
                            else None,
                            ip_address=row["ip_address"],
                            user_agent=row["user_agent"],
                            resource_type=row["resource_type"],
                            resource_id=str(row["resource_id"])
                            if row["resource_id"]
                            else None,
                            details=row["details"] or {},
                            status=row["status"],
                            error_message=row["error_message"],
                            thread_id=str(row["thread_id"])
                            if row["thread_id"]
                            else None,
                            post_id=str(row["post_id"]) if row["post_id"] else None,
                            agent_run_id=str(row["agent_run_id"])
                            if row["agent_run_id"]
                            else None,
                        )
                    )

                return {
                    "logs": logs,
                    "total_count": total,
                    "page": page,
                    "page_size": page_size,
                    "has_more": offset + page_size < total,
                }

        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")
            return {
                "logs": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "has_more": False,
            }

    def _query_memory_logs(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """Query in-memory logs with filters."""
        filtered = list(self._memory_logs.values())

        if event_type:
            filtered = [log for log in filtered if log.event_type.value == event_type]
        if user_id:
            filtered = [log for log in filtered if log.user_id == user_id]
        if resource_type:
            filtered = [log for log in filtered if log.resource_type == resource_type]
        if resource_id:
            filtered = [log for log in filtered if log.resource_id == resource_id]
        if thread_id:
            filtered = [log for log in filtered if log.thread_id == thread_id]
        if status:
            filtered = [log for log in filtered if log.status == status]
        if start_date:
            filtered = [log for log in filtered if log.timestamp >= start_date]
        if end_date:
            filtered = [log for log in filtered if log.timestamp <= end_date]

        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        total_count = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = filtered[start_idx:end_idx]

        return {
            "logs": paginated_logs,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": end_idx < total_count,
        }

    # ========================================================================
    # MEDIA ASSET METHODS
    # ========================================================================

    async def store_media_asset(self, asset: MediaAsset) -> str:
        """
        Store media asset in database.

        Args:
            asset: The media asset to store

        Returns:
            The asset ID
        """
        if not self.is_enabled():
            self._memory_media[asset.id] = asset
            return asset.id

        query = """
            INSERT INTO media_assets (
                id, created_at, asset_type, url, prompt, generated_by,
                service, thread_id, post_id, duration_seconds, thumbnail_url,
                status, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (id) DO UPDATE SET
                url = EXCLUDED.url,
                status = EXCLUDED.status,
                thumbnail_url = EXCLUDED.thumbnail_url
            RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    query,
                    asset.id,
                    asset.created_at,
                    asset.asset_type,
                    asset.url,
                    asset.prompt,
                    asset.generated_by,
                    asset.service,
                    asset.thread_id,
                    asset.post_id,
                    asset.duration_seconds,
                    asset.thumbnail_url,
                    asset.status,
                    json.dumps({}),
                )
                return result["id"]
        except Exception as e:
            logger.error(f"Failed to store media asset: {e}")
            self._memory_media[asset.id] = asset
            return asset.id

    async def get_media_assets(
        self,
        asset_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[MediaAsset]:
        """Get media assets with filters."""
        if not self.is_enabled():
            assets = list(self._memory_media.values())
            if asset_type:
                assets = [a for a in assets if a.asset_type == asset_type]
            if thread_id:
                assets = [a for a in assets if a.thread_id == thread_id]
            if user_id:
                assets = [a for a in assets if a.generated_by == user_id]
            assets.sort(key=lambda x: x.created_at, reverse=True)
            return assets[:limit]

        conditions = []
        params = []
        param_count = 0

        if asset_type:
            param_count += 1
            conditions.append(f"asset_type = ${param_count}")
            params.append(asset_type)

        if thread_id:
            param_count += 1
            conditions.append(f"thread_id = ${param_count}::uuid")
            params.append(thread_id)

        if user_id:
            param_count += 1
            conditions.append(f"generated_by = ${param_count}::uuid")
            params.append(user_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            async with self.pool.acquire() as conn:
                query = f"""
                    SELECT * FROM media_assets
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_count + 1}
                """
                params.append(limit)

                rows = await conn.fetch(query, *params)

                return [
                    MediaAsset(
                        id=str(row["id"]),
                        created_at=row["created_at"],
                        asset_type=row["asset_type"],
                        url=row["url"],
                        prompt=row["prompt"],
                        generated_by=str(row["generated_by"])
                        if row["generated_by"]
                        else "system",
                        service=row["service"],
                        thread_id=str(row["thread_id"]) if row["thread_id"] else None,
                        post_id=str(row["post_id"]) if row["post_id"] else None,
                        duration_seconds=row["duration_seconds"],
                        thumbnail_url=row["thumbnail_url"],
                        status=row["status"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to get media assets: {e}")
            return []

    # ========================================================================
    # CONVERSATION AUDIT METHODS
    # ========================================================================

    async def store_conversation_audit(self, audit: ConversationAudit) -> str:
        """
        Store or update conversation audit in database.

        Args:
            audit: The conversation audit to store

        Returns:
            The audit ID
        """
        if not self.is_enabled():
            self._memory_conversations[audit.thread_id] = audit
            return audit.id

        query = """
            INSERT INTO conversation_audits (
                id, thread_id, created_at, updated_at, participant_ids,
                agent_handles, message_count, human_message_count,
                agent_message_count, media_assets, commands_executed,
                status, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (thread_id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                participant_ids = EXCLUDED.participant_ids,
                agent_handles = EXCLUDED.agent_handles,
                message_count = EXCLUDED.message_count,
                human_message_count = EXCLUDED.human_message_count,
                agent_message_count = EXCLUDED.agent_message_count,
                media_assets = EXCLUDED.media_assets,
                commands_executed = EXCLUDED.commands_executed,
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata
            RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    query,
                    audit.id,
                    audit.thread_id,
                    audit.created_at,
                    audit.updated_at,
                    audit.participant_ids,
                    audit.agent_handles,
                    audit.message_count,
                    audit.human_message_count,
                    audit.agent_message_count,
                    audit.media_assets,
                    audit.commands_executed,
                    audit.status,
                    json.dumps({}),
                )
                return result["id"]
        except Exception as e:
            logger.error(f"Failed to store conversation audit: {e}")
            self._memory_conversations[audit.thread_id] = audit
            return audit.id

    async def get_conversation_audit(
        self, thread_id: str
    ) -> Optional[ConversationAudit]:
        """Get conversation audit for a thread."""
        if not self.is_enabled():
            return self._memory_conversations.get(thread_id)

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM conversation_audits WHERE thread_id = $1",
                    thread_id,
                )

                if not row:
                    return None

                return ConversationAudit(
                    id=str(row["id"]),
                    thread_id=str(row["thread_id"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    participant_ids=row["participant_ids"] or [],
                    agent_handles=row["agent_handles"] or [],
                    message_count=row["message_count"],
                    human_message_count=row["human_message_count"],
                    agent_message_count=row["agent_message_count"],
                    media_assets=[str(m) for m in (row["media_assets"] or [])],
                    commands_executed=row["commands_executed"] or [],
                    status=row["status"],
                )
        except Exception as e:
            logger.error(f"Failed to get conversation audit: {e}")
            return None

    async def get_all_conversation_audits(self) -> List[ConversationAudit]:
        """Get all conversation audits."""
        if not self.is_enabled():
            return list(self._memory_conversations.values())

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM conversation_audits ORDER BY updated_at DESC"
                )

                return [
                    ConversationAudit(
                        id=str(row["id"]),
                        thread_id=str(row["thread_id"]),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        participant_ids=row["participant_ids"] or [],
                        agent_handles=row["agent_handles"] or [],
                        message_count=row["message_count"],
                        human_message_count=row["human_message_count"],
                        agent_message_count=row["agent_message_count"],
                        media_assets=[str(m) for m in (row["media_assets"] or [])],
                        commands_executed=row["commands_executed"] or [],
                        status=row["status"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to get conversation audits: {e}")
            return []

    # ========================================================================
    # STATISTICS METHODS
    # ========================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        if not self.is_enabled():
            return self._get_memory_stats()

        try:
            async with self.pool.acquire() as conn:
                # Get counts
                total_logs = await conn.fetchval("SELECT COUNT(*) FROM audit_logs")
                total_media = await conn.fetchval("SELECT COUNT(*) FROM media_assets")
                total_conversations = await conn.fetchval(
                    "SELECT COUNT(*) FROM conversation_audits"
                )

                # Get event type breakdown
                event_counts = {}
                rows = await conn.fetch(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM audit_logs
                    GROUP BY event_type
                    """
                )
                for row in rows:
                    event_counts[row["event_type"]] = row["count"]

                # Get media counts
                video_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM media_assets WHERE asset_type = 'video'"
                )
                image_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM media_assets WHERE asset_type = 'image'"
                )

                return {
                    "total_logs": total_logs,
                    "total_media_assets": total_media,
                    "total_conversations": total_conversations,
                    "event_type_counts": event_counts,
                    "video_count": video_count,
                    "image_count": image_count,
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return self._get_memory_stats()

    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get stats from in-memory storage."""
        total_logs = len(self._memory_logs)
        total_media = len(self._memory_media)
        total_conversations = len(self._memory_conversations)

        event_counts = {}
        for log in self._memory_logs.values():
            et = log.event_type.value
            event_counts[et] = event_counts.get(et, 0) + 1

        video_count = sum(
            1 for m in self._memory_media.values() if m.asset_type == "video"
        )
        image_count = sum(
            1 for m in self._memory_media.values() if m.asset_type == "image"
        )

        return {
            "total_logs": total_logs,
            "total_media_assets": total_media,
            "total_conversations": total_conversations,
            "event_type_counts": event_counts,
            "video_count": video_count,
            "image_count": image_count,
        }

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    async def export_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
        limit: int = 100000,
    ) -> str:
        """
        Export audit logs in specified format.

        Args:
            start_date: Start date filter
            end_date: End date filter
            format: Export format (json, csv)
            limit: Maximum number of logs to export

        Returns:
            String representation of exported logs
        """
        result = await self.query_audit_logs(
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=limit,
        )

        logs = result["logs"]

        if format == "json":
            return json.dumps([log.dict() for log in logs], default=str)

        elif format == "csv":
            import io

            import csv

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "id",
                    "timestamp",
                    "event_type",
                    "user_id",
                    "resource_type",
                    "resource_id",
                    "status",
                    "thread_id",
                    "post_id",
                    "ip_address",
                    "details",
                ]
            )
            for log in logs:
                writer.writerow(
                    [
                        log.id,
                        log.timestamp,
                        log.event_type.value,
                        log.user_id,
                        log.resource_type,
                        log.resource_id,
                        log.status,
                        log.thread_id,
                        log.post_id,
                        log.ip_address,
                        json.dumps(log.details),
                    ]
                )
            return output.getvalue()

        return str([log.dict() for log in logs])


# Global database service instance
database_service = DatabaseService()
