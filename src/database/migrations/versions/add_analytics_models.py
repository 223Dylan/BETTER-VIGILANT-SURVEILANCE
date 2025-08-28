"""Add analytics models

Revision ID: analytics_models_001
Revises: notification_history_001
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "analytics_models_001"
down_revision = "44f5a96cd98e"
branch_labels = None
depends_on = None


def upgrade():
    # Create detection_metrics table
    op.create_table(
        "detection_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", sa.String(), nullable=False),
        sa.Column("frame_id", sa.String(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prediction_label", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("is_shoplifting", sa.Boolean(), default=False),
        sa.Column(
            "bounding_box", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("object_count", sa.Integer(), default=1),
        sa.Column("processing_time_ms", sa.Float(), nullable=False),
        sa.Column("inference_time_ms", sa.Float(), nullable=False),
        sa.Column("preprocess_time_ms", sa.Float(), nullable=False),
        sa.Column("postprocess_time_ms", sa.Float(), nullable=False),
        sa.Column("fps_actual", sa.Float(), nullable=False),
        sa.Column("fps_target", sa.Float(), nullable=False, default=30.0),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("queue_depth", sa.Integer(), default=0),
        sa.Column("dropped_frames", sa.Integer(), default=0),
        sa.Column("memory_usage_mb", sa.Float(), nullable=True),
        sa.Column("gpu_usage_percent", sa.Float(), nullable=True),
        sa.Column("cpu_usage_percent", sa.Float(), nullable=True),
        sa.Column("alert_triggered", sa.Boolean(), default=False),
        sa.Column("alert_level", sa.String(length=20), nullable=True),
        sa.Column("alert_type", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "location_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "weather_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("lighting_conditions", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_detection_metrics_camera_id", "detection_metrics", ["camera_id"]
    )
    op.create_index(
        "ix_detection_metrics_timestamp", "detection_metrics", ["timestamp"]
    )
    op.create_index("ix_detection_metrics_frame_id", "detection_metrics", ["frame_id"])

    # Create system_metrics table
    op.create_table(
        "system_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostname", sa.String(length=100), nullable=False),
        sa.Column(
            "system_type",
            sa.String(length=50),
            nullable=False,
            default="surveillance_system",
        ),
        sa.Column("cpu_usage_percent", sa.Float(), nullable=False),
        sa.Column("cpu_count", sa.Integer(), nullable=False),
        sa.Column("cpu_frequency_mhz", sa.Float(), nullable=True),
        sa.Column("cpu_temperature_celsius", sa.Float(), nullable=True),
        sa.Column("memory_usage_percent", sa.Float(), nullable=False),
        sa.Column("memory_total_gb", sa.Float(), nullable=False),
        sa.Column("memory_available_gb", sa.Float(), nullable=False),
        sa.Column("memory_used_gb", sa.Float(), nullable=False),
        sa.Column("swap_usage_percent", sa.Float(), nullable=True),
        sa.Column("disk_usage_percent", sa.Float(), nullable=False),
        sa.Column("disk_total_gb", sa.Float(), nullable=False),
        sa.Column("disk_used_gb", sa.Float(), nullable=False),
        sa.Column("disk_free_gb", sa.Float(), nullable=False),
        sa.Column("disk_read_mbps", sa.Float(), nullable=True),
        sa.Column("disk_write_mbps", sa.Float(), nullable=True),
        sa.Column("network_in_mbps", sa.Float(), nullable=True),
        sa.Column("network_out_mbps", sa.Float(), nullable=True),
        sa.Column("network_connections", sa.Integer(), nullable=True),
        sa.Column("gpu_usage_percent", sa.Float(), nullable=True),
        sa.Column("gpu_memory_usage_percent", sa.Float(), nullable=True),
        sa.Column("gpu_temperature_celsius", sa.Float(), nullable=True),
        sa.Column("active_cameras", sa.Integer(), nullable=False, default=0),
        sa.Column("active_detections", sa.Integer(), nullable=False, default=0),
        sa.Column("active_alerts", sa.Integer(), nullable=False, default=0),
        sa.Column("system_load_1min", sa.Float(), nullable=True),
        sa.Column("system_load_5min", sa.Float(), nullable=True),
        sa.Column("system_load_15min", sa.Float(), nullable=True),
        sa.Column("total_processes", sa.Integer(), nullable=True),
        sa.Column("zombie_processes", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("last_boot_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("system_info", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_metrics_timestamp", "system_metrics", ["timestamp"])
    op.create_index("ix_system_metrics_hostname", "system_metrics", ["hostname"])

    # Create camera_metrics table
    op.create_table(
        "camera_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", sa.String(), nullable=False),
        sa.Column(
            "connection_status",
            sa.String(length=20),
            nullable=False,
            default="connected",
        ),
        sa.Column("connection_latency_ms", sa.Float(), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fps_actual", sa.Float(), nullable=False),
        sa.Column("fps_target", sa.Float(), nullable=False, default=30.0),
        sa.Column("resolution_width", sa.Integer(), nullable=True),
        sa.Column("resolution_height", sa.Integer(), nullable=True),
        sa.Column("bitrate_kbps", sa.Integer(), nullable=True),
        sa.Column("frame_processing_time_ms", sa.Float(), nullable=True),
        sa.Column("queue_depth", sa.Integer(), default=0),
        sa.Column("dropped_frames", sa.Integer(), default=0),
        sa.Column("total_frames_processed", sa.Integer(), default=0),
        sa.Column("signal_strength", sa.Float(), nullable=True),
        sa.Column("noise_level", sa.Float(), nullable=True),
        sa.Column("brightness_level", sa.Float(), nullable=True),
        sa.Column("contrast_level", sa.Float(), nullable=True),
        sa.Column("recording_status", sa.Boolean(), default=False),
        sa.Column("storage_used_gb", sa.Float(), nullable=True),
        sa.Column("storage_available_gb", sa.Float(), nullable=True),
        sa.Column("bandwidth_usage_mbps", sa.Float(), nullable=True),
        sa.Column("packet_loss_percent", sa.Float(), nullable=True),
        sa.Column("jitter_ms", sa.Float(), nullable=True),
        sa.Column("error_count", sa.Integer(), default=0),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("error_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "location_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "environmental_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_camera_metrics_camera_id", "camera_metrics", ["camera_id"])
    op.create_index("ix_camera_metrics_timestamp", "camera_metrics", ["timestamp"])

    # Create analytics_aggregates table
    op.create_table(
        "analytics_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregation_type", sa.String(length=50), nullable=False),
        sa.Column("time_period", sa.String(length=20), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("camera_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("total_detections", sa.Integer(), default=0),
        sa.Column("shoplifting_detections", sa.Integer(), default=0),
        sa.Column("false_positives", sa.Integer(), default=0),
        sa.Column("average_confidence", sa.Float(), default=0.0),
        sa.Column("detection_rate_per_hour", sa.Float(), default=0.0),
        sa.Column("total_alerts", sa.Integer(), default=0),
        sa.Column(
            "alerts_by_severity", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "alerts_by_type", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("average_processing_time_ms", sa.Float(), default=0.0),
        sa.Column("average_fps", sa.Float(), default=0.0),
        sa.Column("average_latency_ms", sa.Float(), default=0.0),
        sa.Column("system_uptime_percent", sa.Float(), default=0.0),
        sa.Column("average_cpu_usage", sa.Float(), default=0.0),
        sa.Column("average_memory_usage", sa.Float(), default=0.0),
        sa.Column("average_disk_usage", sa.Float(), default=0.0),
        sa.Column("peak_cpu_usage", sa.Float(), default=0.0),
        sa.Column("peak_memory_usage", sa.Float(), default=0.0),
        sa.Column("active_cameras_count", sa.Integer(), default=0),
        sa.Column(
            "cameras_by_status", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("average_camera_uptime", sa.Float(), default=0.0),
        sa.Column("notifications_sent", sa.Integer(), default=0),
        sa.Column("notifications_delivered", sa.Integer(), default=0),
        sa.Column("notifications_failed", sa.Integer(), default=0),
        sa.Column("average_delivery_time_ms", sa.Float(), default=0.0),
        sa.Column("incidents_resolved", sa.Integer(), default=0),
        sa.Column("average_response_time_minutes", sa.Float(), default=0.0),
        sa.Column("cost_savings_estimate", sa.Float(), default=0.0),
        sa.Column(
            "hourly_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "daily_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_calculated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_completeness_percent", sa.Float(), default=100.0),
        sa.Column("sample_count", sa.Integer(), default=0),
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_aggregates_aggregation_type",
        "analytics_aggregates",
        ["aggregation_type"],
    )
    op.create_index(
        "ix_analytics_aggregates_time_period", "analytics_aggregates", ["time_period"]
    )
    op.create_index(
        "ix_analytics_aggregates_start_time", "analytics_aggregates", ["start_time"]
    )
    op.create_index(
        "ix_analytics_aggregates_camera_id", "analytics_aggregates", ["camera_id"]
    )
    op.create_index(
        "ix_analytics_aggregates_user_id", "analytics_aggregates", ["user_id"]
    )


def downgrade():
    op.drop_index("ix_analytics_aggregates_user_id", table_name="analytics_aggregates")
    op.drop_index(
        "ix_analytics_aggregates_camera_id", table_name="analytics_aggregates"
    )
    op.drop_index(
        "ix_analytics_aggregates_start_time", table_name="analytics_aggregates"
    )
    op.drop_index(
        "ix_analytics_aggregates_time_period", table_name="analytics_aggregates"
    )
    op.drop_index(
        "ix_analytics_aggregates_aggregation_type", table_name="analytics_aggregates"
    )
    op.drop_table("analytics_aggregates")

    op.drop_index("ix_camera_metrics_timestamp", table_name="camera_metrics")
    op.drop_index("ix_camera_metrics_camera_id", table_name="camera_metrics")
    op.drop_table("camera_metrics")

    op.drop_index("ix_system_metrics_hostname", table_name="system_metrics")
    op.drop_index("ix_system_metrics_timestamp", table_name="system_metrics")
    op.drop_table("system_metrics")

    op.drop_index("ix_detection_metrics_frame_id", table_name="detection_metrics")
    op.drop_index("ix_detection_metrics_timestamp", table_name="detection_metrics")
    op.drop_index("ix_detection_metrics_camera_id", table_name="detection_metrics")
    op.drop_table("detection_metrics")
