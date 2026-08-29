import clickhouse_connect
from config import Config

class ClickHouseManager:
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """Establishes connection to ClickHouse Cloud Service."""
        try:
            self.client = clickhouse_connect.get_client(
                host=Config.CLICKHOUSE_HOST,
                port=Config.CLICKHOUSE_PORT,
                username=Config.CLICKHOUSE_USER,
                password=Config.CLICKHOUSE_PASSWORD,
                secure=True
            )
            self._initialize_tables()
            print("[ClickHouse] Successfully connected to cloud instance.")
        except Exception as e:
            print(f"[ClickHouse Error] Connection failed: {str(e)}")
            self.client = None

    def _initialize_tables(self):
        """Creates tables for agent telemetry and identity violation logs."""
        if not self.client:
            return

        # 1. Detection Telemetry Table
        self.client.command('''
            CREATE TABLE IF NOT EXISTS detection_telemetry (
                session_id String,
                timestamp DateTime DEFAULT now(),
                agent_name String,
                anomaly_score Float32,
                status String,
                details String
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        ''')

        # 2. Identity Violation & Takedown Log Table
        self.client.command('''
            CREATE TABLE IF NOT EXISTS identity_takedowns (
                request_id String,
                timestamp DateTime DEFAULT now(),
                target_url String,
                similarity_score Float32,
                notice_type String,
                action_status String
            ) ENGINE = MergeTree()
            ORDER BY timestamp
        ''')

    def log_agent_execution(self, session_id: str, agent_name: str, anomaly_score: float, status: str, details: str):
        """Logs individual agent execution telemetry."""
        if not self.client:
            return False
        try:
            self.client.insert(
                'detection_telemetry',
                [[session_id, agent_name, anomaly_score, status, details]],
                column_names=['session_id', 'agent_name', 'anomaly_score', 'status', 'details']
            )
            return True
        except Exception as e:
            print(f"[ClickHouse Log Error]: {str(e)}")
            return False

    def log_takedown_request(self, request_id: str, target_url: str, similarity_score: float, notice_type: str):
        """Logs legal DMCA and Cyber Crime report generations."""
        if not self.client:
            return False
        try:
            self.client.insert(
                'identity_takedowns',
                [[request_id, target_url, similarity_score, notice_type, "GENERATED"]],
                column_names=['request_id', 'target_url', 'similarity_score', 'notice_type', 'action_status']
            )
            return True
        except Exception as e:
            print(f"[ClickHouse Takedown Log Error]: {str(e)}")
            return False

# Shared Instance
db_manager = ClickHouseManager()