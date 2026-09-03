from config import Config

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None


class ClickHouseManager:
    def __init__(self):
        self.client = None
        self.last_error = None
        self._connect()

    @property
    def configured(self) -> bool:
        return Config.clickhouse_configured()

    def _connect(self):
        """Connect only when ClickHouse credentials are configured."""
        if not self.configured:
            print("[ClickHouse] Not configured yet; telemetry disabled.")
            return
        if clickhouse_connect is None:
            self.last_error = "clickhouse-connect package is not installed"
            print(f"[ClickHouse] {self.last_error}")
            return

        try:
            self.client = clickhouse_connect.get_client(
                host=Config.CLICKHOUSE_HOST,
                port=Config.CLICKHOUSE_PORT,
                username=Config.CLICKHOUSE_USER,
                password=Config.CLICKHOUSE_PASSWORD,
                database=Config.CLICKHOUSE_DATABASE,
                secure=True,
            )
            self.client.command("SELECT 1")
            self._initialize_tables()
            print("[ClickHouse] Successfully connected to cloud instance.")
        except Exception as exc:
            self.last_error = str(exc)
            print(f"[ClickHouse Error] Connection failed: {self.last_error}")
            self.client = None

    def _initialize_tables(self):
        if not self.client:
            return

        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS detection_telemetry (
                session_id String,
                timestamp DateTime DEFAULT now(),
                agent_name String,
                anomaly_score Float32,
                status String,
                details String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, session_id)
            """
        )

        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS identity_takedowns (
                request_id String,
                timestamp DateTime DEFAULT now(),
                target_url String,
                similarity_score Float32,
                notice_type String,
                action_status String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, request_id)
            """
        )

    def log_agent_execution(
        self,
        session_id: str,
        agent_name: str,
        anomaly_score: float,
        status: str,
        details: str,
    ) -> bool:
        if not self.client:
            return False
        try:
            self.client.insert(
                "detection_telemetry",
                [[session_id, agent_name, float(anomaly_score), status, str(details)]],
                column_names=[
                    "session_id",
                    "agent_name",
                    "anomaly_score",
                    "status",
                    "details",
                ],
            )
            return True
        except Exception as exc:
            print(f"[ClickHouse Log Error] {exc}")
            return False

    def log_takedown_request(
        self,
        request_id: str,
        target_url: str,
        similarity_score: float,
        notice_type: str,
    ) -> bool:
        if not self.client:
            return False
        try:
            self.client.insert(
                "identity_takedowns",
                [[request_id, target_url, float(similarity_score), notice_type, "GENERATED"]],
                column_names=[
                    "request_id",
                    "target_url",
                    "similarity_score",
                    "notice_type",
                    "action_status",
                ],
            )
            return True
        except Exception as exc:
            print(f"[ClickHouse Takedown Log Error] {exc}")
            return False


db_manager = ClickHouseManager()
