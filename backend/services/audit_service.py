"""
Audit Service - Enterprise-grade audit trail logging.
Tracks all significant events in the system for compliance and debugging.

Integrates with PostgreSQL for permanent storage when available.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from models import AuditLog, AuditEventType, MediaAsset, ConversationAudit

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for tracking and querying audit logs.

    Features:
    - In-memory caching for fast access
    - PostgreSQL backend for permanent storage
    - Automatic sync between cache and database
    - Export capabilities for compliance
    """

    def __init__(self):
        # In-memory storage for audit logs (cache)
        self._logs: Dict[str, AuditLog] = {}
        self._media_assets: Dict[str, MediaAsset] = {}
        self._conversation_audits: Dict[str, ConversationAudit] = {}
        self._database_service = None

    def set_database_service(self, db_service):
        """Set the database service for persistent storage."""
        self._database_service = db_service

    async def _store_to_database(self, log: AuditLog):
        """Async store log to database if available."""
        if self._database_service:
            try:
                await self._database_service.store_audit_log(log)
            except Exception as e:
                logger.warning(f"Failed to store audit log to database: {e}")
    """Service for tracking and querying audit logs"""

    def __init__(self):
        # In-memory storage for audit logs
        self._logs: Dict[str, AuditLog] = {}
        self._media_assets: Dict[str, MediaAsset] = {}
        self._conversation_audits: Dict[str, ConversationAudit] = {}

    # ========================================================================
    # LOGGING METHODS
    # ========================================================================

    async def log_event(
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        thread_id: Optional[str] = None,
        post_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            event_type: Type of event from AuditEventType
            user_id: User who performed the action
            resource_type: Type of resource affected (post, agent_run, etc.)
            resource_id: ID of the affected resource
            details: Additional event details
            status: Event status (success, failed, pending)
            error_message: Error message if status is failed
            thread_id: Related thread ID
            post_id: Related post ID
            agent_run_id: Related agent run ID
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier

        Returns:
            The created AuditLog entry
        """
        log_id = str(uuid.uuid4())
        log = AuditLog(
            id=log_id,
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            status=status,
            error_message=error_message,
            thread_id=thread_id,
            post_id=post_id,
            agent_run_id=agent_run_id,
        )

        self._logs[log_id] = log

        # Store to database asynchronously
        await self._store_to_database(log)

        # Log to standard logger for immediate visibility
        log_level = logging.ERROR if status == "failed" else logging.INFO
        logger.log(
            log_level,
            f"[{event_type.value}] user={user_id} resource={resource_type}:{resource_id} status={status}",
        )

        return log

    def log_event_sync(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        thread_id: Optional[str] = None,
        post_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Synchronous version of log_event for use in non-async contexts.

        Returns immediately without waiting for database storage.
        Database write happens in the background if available.
        """
        import asyncio

        log_id = str(uuid.uuid4())
        log = AuditLog(
            id=log_id,
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            status=status,
            error_message=error_message,
            thread_id=thread_id,
            post_id=post_id,
            agent_run_id=agent_run_id,
        )

        self._logs[log_id] = log

        # Schedule database write without blocking
        if self._database_service:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._store_to_database(log))
            except RuntimeError:
                pass  # No event loop running, skip database write

        # Log to standard logger
        log_level = logging.ERROR if status == "failed" else logging.INFO
        logger.log(
            log_level,
            f"[{event_type.value}] user={user_id} resource={resource_type}:{resource_id} status={status}",
        )

        return log

    def log_post_create(
        self,
        post_id: str,
        user_id: str,
        text: str,
        thread_id: str,
        parent_id: Optional[str] = None,
    ) -> AuditLog:
        """Log post creation"""
        return self.log_event_sync(
        return self.log_event(
            event_type=AuditEventType.POST_CREATE,
            user_id=user_id,
            resource_type="post",
            resource_id=post_id,
            details={
                "text": text[:200],  # Truncate long text
                "parent_id": parent_id,
            },
            thread_id=thread_id,
            post_id=post_id,
        )

    def log_post_delete(
        self,
        post_id: str,
        user_id: str,
        thread_id: Optional[str] = None,
    ) -> AuditLog:
        """Log post deletion"""
        return self.log_event_sync(
        return self.log_event(
            event_type=AuditEventType.POST_DELETE,
            user_id=user_id,
            resource_type="post",
            resource_id=post_id,
            thread_id=thread_id,
            post_id=post_id,
        )

    def log_agent_run(
        self,
        agent_run_id: str,
        agent_handle: str,
        thread_id: str,
        trigger_post_id: str,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log agent run execution"""
        event_type = (
            AuditEventType.AGENT_RUN_ERROR
            if status == "failed"
            else AuditEventType.AGENT_RUN_COMPLETE
        )

        # Also log start event if this is a completion
        if status == "running":
            return self.log_event_sync(
            return self.log_event(
                event_type=AuditEventType.AGENT_RUN_START,
                resource_type="agent_run",
                resource_id=agent_run_id,
                details={
                    "agent_handle": agent_handle,
                    "trigger_post_id": trigger_post_id,
                },
                thread_id=thread_id,
                agent_run_id=agent_run_id,
            )

        return self.log_event_sync(
        return self.log_event(
            event_type=event_type,
            resource_type="agent_run",
            resource_id=agent_run_id,
            details={
                "agent_handle": agent_handle,
                "trigger_post_id": trigger_post_id,
            },
            status=status,
            error_message=error_message,
            thread_id=thread_id,
            agent_run_id=agent_run_id,
        )

    def log_media_generation(
        self,
        asset_type: str,  # "video" or "image"
        url: str,
        prompt: str,
        user_id: Optional[str] = None,
        service: str = "klingai",
        thread_id: Optional[str] = None,
        post_id: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> tuple[MediaAsset, AuditLog]:
        """
        Log media generation and create a media asset record.

        Returns:
            Tuple of (MediaAsset, AuditLog)
        """
        # Create media asset record
        asset_id = str(uuid.uuid4())
        asset = MediaAsset(
            id=asset_id,
            created_at=datetime.now(),
            asset_type=asset_type,  # type: ignore
            url=url,
            prompt=prompt,
            generated_by=user_id or "system",
            service=service,
            thread_id=thread_id,
            post_id=post_id,
            duration_seconds=duration_seconds,
            status=status,
        )
        self._media_assets[asset_id] = asset

        # Log the event
        event_type = (
            AuditEventType.MEDIA_VIDEO_GENERATE
            if asset_type == "video"
            else AuditEventType.MEDIA_IMAGE_GENERATE
        )

        # Store to database if available
        if self._database_service:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._database_service.store_media_asset(asset))
            except RuntimeError:
                pass  # No event loop

        log = self.log_event_sync(
        log = self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="media",
            resource_id=asset_id,
            details={
                "asset_type": asset_type,
                "url": url,
                "prompt": prompt[:200],
                "service": service,
                "duration_seconds": duration_seconds,
            },
            status=status,
            error_message=error_message,
            thread_id=thread_id,
            post_id=post_id,
        )

        return asset, log

    def log_auth_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        provider: str = "unknown",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log authentication events"""
        return self.log_event_sync(
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="auth",
            details={
                "email": email,
                "provider": provider,
            },
            status="failed" if event_type == AuditEventType.AUTH_FAILED else "success",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_command_execution(
        self,
        command: str,
        args: Dict[str, Any],
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log slash command execution"""
        event_type = (
            AuditEventType.COMMAND_FAILED
            if status == "failed"
            else AuditEventType.COMMAND_EXECUTED
        )

        return self.log_event_sync(
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="command",
            resource_id=command,
            details={
                "command": command,
                "args": args,
            },
            status=status,
            error_message=error_message,
            thread_id=thread_id,
        )

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    async def get_logs(
    def get_logs(
        self,
        event_type: Optional[AuditEventType] = None,
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

        Returns:
            Dict with logs list and pagination info
        """
        # If database is available, query from database
        if self._database_service:
            try:
                return await self._database_service.query_audit_logs(
                    event_type=event_type.value if event_type else None,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    thread_id=thread_id,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    search_query=search_query,
                    page=page,
                    page_size=page_size,
                )
            except Exception as e:
                logger.warning(f"Database query failed, falling back to memory: {e}")

        # Fallback to in-memory query
        filtered = list(self._logs.values())

        # Apply filters
        if event_type:
            filtered = [log for log in filtered if log.event_type == event_type]
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
        if search_query:
            filtered = [
                log
                for log in filtered
                if search_query.lower() in str(log.details).lower()
                or (
                    log.error_message
                    and search_query.lower() in log.error_message.lower()
                )
            ]

        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        # Pagination
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

    def get_logs_sync(
        self,
        event_type: Optional[AuditEventType] = None,
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
        """
        Synchronous version of get_logs for backwards compatibility.
        Only queries in-memory cache.
        """
        # Start with all logs
        filtered = list(self._logs.values())

        # Apply filters
        if event_type:
            filtered = [log for log in filtered if log.event_type == event_type]
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

        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        # Pagination
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

    def get_media_assets(
        self,
        asset_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[MediaAsset]:
        """Get media assets with filters"""
        assets = list(self._media_assets.values())

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        if thread_id:
            assets = [a for a in assets if a.thread_id == thread_id]
        if user_id:
            assets = [a for a in assets if a.generated_by == user_id]

        assets.sort(key=lambda x: x.created_at, reverse=True)
        return assets[:limit]

    def get_or_create_conversation_audit(self, thread_id: str) -> ConversationAudit:
    def get_or_create_conversation_audit(
        self, thread_id: str
    ) -> ConversationAudit:
        """Get or create conversation audit for a thread"""
        if thread_id in self._conversation_audits:
            return self._conversation_audits[thread_id]

        audit = ConversationAudit(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._conversation_audits[thread_id] = audit
        return audit

    def update_conversation_audit(
        self,
        thread_id: str,
        participant_id: Optional[str] = None,
        agent_handle: Optional[str] = None,
        media_asset_id: Optional[str] = None,
        command: Optional[str] = None,
    ):
        """Update conversation audit with new activity"""
        audit = self.get_or_create_conversation_audit(thread_id)
        audit.updated_at = datetime.now()

        if participant_id and participant_id not in audit.participant_ids:
            audit.participant_ids.append(participant_id)
        if agent_handle and agent_handle not in audit.agent_handles:
            audit.agent_handles.append(agent_handle)
        if media_asset_id and media_asset_id not in audit.media_assets:
            audit.media_assets.append(media_asset_id)
        if command and command not in audit.commands_executed:
            audit.commands_executed.append(command)

    def get_conversation_audit(self, thread_id: str) -> Optional[ConversationAudit]:
        """Get conversation audit for a thread"""
        return self._conversation_audits.get(thread_id)

    def get_all_conversation_audits(self) -> List[ConversationAudit]:
        """Get all conversation audits"""
        return list(self._conversation_audits.values())

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    def export_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """
        Export audit logs for external storage/analysis.

        Args:
            start_date: Start date filter
            end_date: End date filter
            format: Export format (json, csv)

        Returns:
            String representation of exported logs
        """
        logs = self.get_logs_sync(
            start_date=start_date, end_date=end_date, page_size=10000
        )["logs"]
        logs = self.get_logs(start_date=start_date, end_date=end_date, page_size=10000)[
            "logs"
        ]

        if format == "json":
            import json

            return json.dumps([log.dict() for log in logs], default=str)

        elif format == "csv":
            import io

            import csv

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "timestamp",
                    "event_type",
                    "user_id",
                    "resource_type",
                    "resource_id",
                    "status",
                    "thread_id",
                ]
            )
            for log in logs:
                writer.writerow(
                    [
                        log.timestamp,
                        log.event_type.value,
                        log.user_id,
                        log.resource_type,
                        log.resource_id,
                        log.status,
                        log.thread_id,
                    ]
                )
            return output.getvalue()

        return str([log.dict() for log in logs])

    def get_stats(self) -> Dict[str, Any]:
        """Get audit trail statistics"""
        total_logs = len(self._logs)
        total_media = len(self._media_assets)
        total_conversations = len(self._conversation_audits)

        # Count by event type
        event_counts: Dict[str, int] = {}
        for log in self._logs.values():
            et = log.event_type.value
            event_counts[et] = event_counts.get(et, 0) + 1

        # Count media by type
        video_count = sum(
            1 for m in self._media_assets.values() if m.asset_type == "video"
        )
        image_count = sum(
            1 for m in self._media_assets.values() if m.asset_type == "image"
        )
        video_count = sum(1 for m in self._media_assets.values() if m.asset_type == "video")
        image_count = sum(1 for m in self._media_assets.values() if m.asset_type == "image")

        return {
            "total_logs": total_logs,
            "total_media_assets": total_media,
            "total_conversations": total_conversations,
            "event_type_counts": event_counts,
            "video_count": video_count,
            "image_count": image_count,
        }


# Global audit service instance
audit_service = AuditService()
