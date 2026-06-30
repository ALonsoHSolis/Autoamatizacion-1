from __future__ import annotations

import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, MutableMapping
from urllib.parse import unquote, urlparse

import pandas as pd

from src.utils import clean_column_names, parse_date_series, parse_numeric_series


MIGRATION_PATH = Path(__file__).resolve().parent.parent / "migrations" / "001_treasury_tower.sql"
TREASURY_DB_ENV = "TREASURY_DATABASE_URL"
DATABASE_URL_ENV = "DATABASE_URL"


def database_url_from_env() -> str | None:
    return os.getenv(TREASURY_DB_ENV) or os.getenv(DATABASE_URL_ENV)


def mysql_config_from_env() -> dict[str, Any] | None:
    url = database_url_from_env()
    if url:
        return _parse_mysql_url(url)

    database = os.getenv("TREASURY_DB_NAME")
    user = os.getenv("TREASURY_DB_USER")
    if not database or not user:
        return None

    return {
        "host": os.getenv("TREASURY_DB_HOST", "localhost"),
        "port": int(os.getenv("TREASURY_DB_PORT", "3306")),
        "user": user,
        "password": os.getenv("TREASURY_DB_PASSWORD", ""),
        "database": database,
    }


def _parse_mysql_url(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise RuntimeError(
            "TREASURY_DATABASE_URL debe usar mysql+pymysql://usuario:password@host:3306/base."
        )
    if not parsed.hostname or not parsed.username or not parsed.path.strip("/"):
        raise RuntimeError("TREASURY_DATABASE_URL debe incluir host, usuario y nombre de base de datos.")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username),
        "password": unquote(parsed.password or ""),
        "database": unquote(parsed.path.lstrip("/")),
    }


def _migration_statements(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def parse_treasury_balances(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Validate and normalize balance uploads for treasury_saldos_diarios."""
    clean_df = clean_column_names(df.copy())
    aliases = {
        "cuenta": ["cuenta", "nombre_cuenta", "account", "account_name"],
        "fecha": ["fecha", "date"],
        "saldo_interno": ["saldo_interno", "saldo", "monto", "balance", "saldo_contable"],
        "saldo_extracto": ["saldo_extracto", "extracto", "saldo_banco", "bank_balance"],
        "banco": ["banco", "bank"],
        "moneda": ["moneda", "currency"],
        "reserva_minima": ["reserva_minima", "reserva", "minimum_reserve"],
    }

    resolved: dict[str, str] = {}
    for target, candidates in aliases.items():
        for candidate in candidates:
            if candidate in clean_df.columns:
                resolved[target] = candidate
                break

    missing = [name for name in ("cuenta", "fecha", "saldo_interno") if name not in resolved]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Faltan columnas obligatorias: {missing_text}. Usa cuenta, fecha y saldo.")

    normalized = pd.DataFrame()
    normalized["cuenta"] = clean_df[resolved["cuenta"]].astype(str).str.strip()
    normalized["cuenta"] = normalized["cuenta"].mask(
        normalized["cuenta"].str.lower().isin(["", "nan", "none", "null"])
    )
    normalized["fecha"] = parse_date_series(clean_df[resolved["fecha"]]).dt.date
    normalized["saldo_interno"] = parse_numeric_series(clean_df[resolved["saldo_interno"]])

    if "saldo_extracto" in resolved:
        normalized["saldo_extracto"] = parse_numeric_series(clean_df[resolved["saldo_extracto"]])
    else:
        normalized["saldo_extracto"] = pd.NA
    normalized["banco"] = clean_df[resolved["banco"]].astype(str).str.strip() if "banco" in resolved else ""
    normalized["moneda"] = clean_df[resolved["moneda"]].astype(str).str.strip() if "moneda" in resolved else "CLP"
    normalized["reserva_minima"] = (
        parse_numeric_series(clean_df[resolved["reserva_minima"]]) if "reserva_minima" in resolved else 0
    )
    normalized["fuente"] = source

    normalized = normalized.dropna(subset=["cuenta", "fecha", "saldo_interno"])
    normalized = normalized[normalized["cuenta"].str.len() > 0]
    if normalized.empty:
        raise ValueError("No hay filas validas para cargar saldos.")
    return normalized


def _to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class MemoryTreasuryRepository:
    """Session-friendly fallback used when no MySQL connection is configured."""

    backend_name = "demo_en_memoria"

    def __init__(self, store: MutableMapping[str, Any] | None = None):
        self.store = store if store is not None else {}
        self._ensure_seed()

    @property
    def is_mysql(self) -> bool:
        return False

    def initialize_schema(self) -> None:
        self._ensure_seed()

    def _ensure_seed(self) -> None:
        self.store.setdefault("next_ids", {
            "cuenta": 4,
            "saldo": 4,
            "discrepancia": 1,
            "accion": 1,
            "informe": 1,
            "nota": 1,
        })
        today = date.today()
        self.store.setdefault("cuentas", [
            {"id": 1, "nombre": "Cuenta Operativa", "banco": "Banco Estado", "moneda": "CLP", "reserva_minima": 2_500_000.0, "activa": True},
            {"id": 2, "nombre": "Cuenta Proveedores", "banco": "Santander", "moneda": "CLP", "reserva_minima": 1_250_000.0, "activa": True},
            {"id": 3, "nombre": "Cuenta Recaudacion", "banco": "BCI", "moneda": "CLP", "reserva_minima": 1_000_000.0, "activa": True},
        ])
        self.store.setdefault("saldos", [
            {"id": 1, "cuenta_id": 1, "fecha": today, "saldo_interno": 7_820_000.0, "saldo_extracto": 7_800_000.0, "fuente": "demo", "cargado_por": "demo", "cargado_en": datetime.now()},
            {"id": 2, "cuenta_id": 2, "fecha": today, "saldo_interno": 1_080_000.0, "saldo_extracto": 1_080_000.0, "fuente": "demo", "cargado_por": "demo", "cargado_en": datetime.now()},
            {"id": 3, "cuenta_id": 3, "fecha": today, "saldo_interno": 3_430_000.0, "saldo_extracto": 3_450_000.0, "fuente": "demo", "cargado_por": "demo", "cargado_en": datetime.now()},
        ])
        self.store.setdefault("discrepancias", [])
        self.store.setdefault("acciones", [])
        self.store.setdefault("informes", [])
        self.store.setdefault("notas", [])

    def _next_id(self, key: str) -> int:
        value = self.store["next_ids"][key]
        self.store["next_ids"][key] += 1
        return value

    def upsert_balances(self, df: pd.DataFrame, fuente: str, cargado_por: str | None = None) -> int:
        normalized = parse_treasury_balances(df, fuente)
        count = 0
        for _, row in normalized.iterrows():
            account = self._get_or_create_account(
                str(row["cuenta"]),
                banco=str(row.get("banco") or ""),
                moneda=str(row.get("moneda") or "CLP"),
                reserva_minima=_to_float(row.get("reserva_minima")) or 0,
            )
            existing = next(
                (item for item in self.store["saldos"] if item["cuenta_id"] == account["id"] and item["fecha"] == row["fecha"]),
                None,
            )
            payload = {
                "cuenta_id": account["id"],
                "fecha": row["fecha"],
                "saldo_interno": _to_float(row["saldo_interno"]) or 0,
                "saldo_extracto": _to_float(row.get("saldo_extracto")),
                "fuente": fuente,
                "cargado_por": cargado_por,
                "cargado_en": datetime.now(),
            }
            if existing:
                existing.update(payload)
            else:
                payload["id"] = self._next_id("saldo")
                self.store["saldos"].append(payload)
            count += 1
        return count

    def _get_or_create_account(self, nombre: str, banco: str, moneda: str, reserva_minima: float) -> dict[str, Any]:
        existing = next((item for item in self.store["cuentas"] if item["nombre"].lower() == nombre.lower()), None)
        if existing:
            existing.update({
                "banco": banco or existing.get("banco"),
                "moneda": moneda or existing.get("moneda") or "CLP",
                "reserva_minima": reserva_minima if reserva_minima else existing.get("reserva_minima", 0),
                "activa": True,
            })
            return existing
        account = {
            "id": self._next_id("cuenta"),
            "nombre": nombre,
            "banco": banco,
            "moneda": moneda or "CLP",
            "reserva_minima": reserva_minima,
            "activa": True,
        }
        self.store["cuentas"].append(account)
        return account

    def latest_balances(self) -> pd.DataFrame:
        rows = []
        for account in self.store["cuentas"]:
            if not account.get("activa", True):
                continue
            account_balances = [item for item in self.store["saldos"] if item["cuenta_id"] == account["id"]]
            latest = max(account_balances, key=lambda item: item["fecha"], default=None)
            saldo = latest["saldo_interno"] if latest else 0
            reserva = account.get("reserva_minima", 0) or 0
            rows.append({
                "cuenta_id": account["id"],
                "cuenta": account["nombre"],
                "banco": account.get("banco", ""),
                "moneda": account.get("moneda", "CLP"),
                "fecha": latest["fecha"] if latest else None,
                "saldo_interno": saldo,
                "saldo_extracto": latest.get("saldo_extracto") if latest else None,
                "reserva_minima": reserva,
                "estado": "OK" if saldo >= reserva else "Alerta",
            })
        return pd.DataFrame(rows)

    def balances_for_date(self, target_date: date) -> pd.DataFrame:
        rows = []
        for saldo in self.store["saldos"]:
            if saldo["fecha"] != target_date:
                continue
            account = next((item for item in self.store["cuentas"] if item["id"] == saldo["cuenta_id"]), {})
            saldo_extracto = saldo.get("saldo_extracto")
            diferencia = saldo["saldo_interno"] - saldo_extracto if saldo_extracto is not None else None
            rows.append({
                "saldo_diario_id": saldo["id"],
                "cuenta": account.get("nombre", ""),
                "moneda": account.get("moneda", "CLP"),
                "fecha": saldo["fecha"],
                "saldo_interno": saldo["saldo_interno"],
                "saldo_extracto": saldo_extracto,
                "diferencia": diferencia,
            })
        return pd.DataFrame(rows)

    def detect_discrepancies(self, target_date: date) -> int:
        balances = self.balances_for_date(target_date)
        created = 0
        for _, row in balances.iterrows():
            if pd.isna(row.get("saldo_extracto")) or not row.get("diferencia"):
                continue
            if abs(float(row["diferencia"])) < 0.01:
                continue
            existing = next(
                (
                    item for item in self.store["discrepancias"]
                    if item["saldo_diario_id"] == row["saldo_diario_id"] and item["estado"] == "abierta"
                ),
                None,
            )
            if not existing:
                self.store["discrepancias"].append({
                    "id": self._next_id("discrepancia"),
                    "saldo_diario_id": int(row["saldo_diario_id"]),
                    "diferencia": float(row["diferencia"]),
                    "estado": "abierta",
                    "detectada_en": datetime.now(),
                })
                created += 1
        return created

    def open_discrepancies(self, target_date: date | None = None) -> pd.DataFrame:
        rows = []
        for disc in self.store["discrepancias"]:
            if disc["estado"] != "abierta":
                continue
            saldo = next((item for item in self.store["saldos"] if item["id"] == disc["saldo_diario_id"]), None)
            if not saldo or (target_date and saldo["fecha"] != target_date):
                continue
            account = next((item for item in self.store["cuentas"] if item["id"] == saldo["cuenta_id"]), {})
            rows.append({**disc, "cuenta": account.get("nombre", ""), "fecha": saldo["fecha"]})
        return pd.DataFrame(rows)

    def register_action(self, discrepancy_id: int, descripcion: str, registrado_por: str | None = None) -> None:
        self.store["acciones"].append({
            "id": self._next_id("accion"),
            "discrepancia_id": discrepancy_id,
            "descripcion": descripcion,
            "registrado_por": registrado_por,
            "registrado_en": datetime.now(),
        })
        for disc in self.store["discrepancias"]:
            if disc["id"] == discrepancy_id:
                disc["estado"] = "cerrada"

    def actions_for_date(self, target_date: date | None = None) -> pd.DataFrame:
        rows = []
        for action in self.store["acciones"]:
            disc = next((item for item in self.store["discrepancias"] if item["id"] == action["discrepancia_id"]), None)
            if not disc:
                continue
            saldo = next((item for item in self.store["saldos"] if item["id"] == disc["saldo_diario_id"]), None)
            if not saldo or (target_date and saldo["fecha"] != target_date):
                continue
            account = next((item for item in self.store["cuentas"] if item["id"] == saldo["cuenta_id"]), {})
            rows.append({**action, "cuenta": account.get("nombre", ""), "fecha": saldo["fecha"], "diferencia": disc["diferencia"]})
        return pd.DataFrame(rows)

    def period_data(self, start_date: date, end_date: date) -> tuple[pd.DataFrame, pd.DataFrame]:
        saldos = []
        for saldo in self.store["saldos"]:
            if start_date <= saldo["fecha"] <= end_date:
                account = next((item for item in self.store["cuentas"] if item["id"] == saldo["cuenta_id"]), {})
                saldos.append({**saldo, "cuenta": account.get("nombre", ""), "moneda": account.get("moneda", "CLP")})
        acciones = self.actions_for_date()
        if not acciones.empty:
            acciones = acciones[(acciones["fecha"] >= start_date) & (acciones["fecha"] <= end_date)]
        return pd.DataFrame(saldos), acciones

    def save_report(self, start_date: date, end_date: date, modules: list[str], fmt: str, generado_por: str | None, filename: str, content: bytes) -> int:
        report_id = self._next_id("informe")
        self.store["informes"].append({
            "id": report_id,
            "periodo_desde": start_date,
            "periodo_hasta": end_date,
            "modulos_incluidos": modules,
            "formato": fmt,
            "generado_por": generado_por,
            "generado_en": datetime.now(),
            "nombre_archivo": filename,
            "contenido": content,
        })
        return report_id

    def recent_reports(self) -> pd.DataFrame:
        return pd.DataFrame(sorted(self.store["informes"], key=lambda item: item["generado_en"], reverse=True))

    def notes(self) -> pd.DataFrame:
        return pd.DataFrame(sorted(self.store["notas"], key=lambda item: item["creado_en"], reverse=True))

    def add_note(self, autor: str, area: str, mensaje: str) -> None:
        self.store["notas"].append({
            "id": self._next_id("nota"),
            "autor": autor,
            "area": area,
            "mensaje": mensaje,
            "creado_en": datetime.now(),
        })


class MySQLTreasuryRepository:
    backend_name = "mysql"

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @property
    def is_mysql(self) -> bool:
        return True

    def _connect(self):
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError("Instala PyMySQL para conectar Treasury Tower a MySQL.") from exc
        return pymysql.connect(
            host=self.config["host"],
            port=int(self.config["port"]),
            user=self.config["user"],
            password=self.config.get("password") or "",
            database=self.config["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def initialize_schema(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        with self._connect() as conn:
            with conn.cursor() as cur:
                for statement in _migration_statements(sql):
                    cur.execute(statement)

    def upsert_balances(self, df: pd.DataFrame, fuente: str, cargado_por: str | None = None) -> int:
        normalized = parse_treasury_balances(df, fuente)
        with self._connect() as conn:
            with conn.cursor() as cur:
                for _, row in normalized.iterrows():
                    cur.execute(
                        """
                        INSERT INTO treasury_cuentas (nombre, banco, moneda, reserva_minima, activa)
                        VALUES (%s, %s, %s, %s, TRUE)
                        ON DUPLICATE KEY UPDATE
                            id = LAST_INSERT_ID(id),
                            banco = COALESCE(VALUES(banco), banco),
                            moneda = VALUES(moneda),
                            reserva_minima = GREATEST(reserva_minima, VALUES(reserva_minima)),
                            activa = TRUE
                        """,
                        (
                            row["cuenta"],
                            row.get("banco") or None,
                            row.get("moneda") or "CLP",
                            _to_float(row.get("reserva_minima")) or 0,
                        ),
                    )
                    account_id = cur.lastrowid
                    cur.execute(
                        """
                        INSERT INTO treasury_saldos_diarios
                            (cuenta_id, fecha, saldo_interno, saldo_extracto, fuente, cargado_por)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            saldo_interno = VALUES(saldo_interno),
                            saldo_extracto = VALUES(saldo_extracto),
                            fuente = VALUES(fuente),
                            cargado_por = VALUES(cargado_por),
                            cargado_en = CURRENT_TIMESTAMP
                        """,
                        (
                            account_id,
                            row["fecha"],
                            _to_float(row["saldo_interno"]) or 0,
                            _to_float(row.get("saldo_extracto")),
                            fuente,
                            cargado_por,
                        ),
                    )
        return len(normalized)

    def latest_balances(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                """
                SELECT c.id AS cuenta_id, c.nombre AS cuenta, c.banco, c.moneda,
                       s.fecha, COALESCE(s.saldo_interno, 0) AS saldo_interno,
                       s.saldo_extracto, c.reserva_minima,
                       CASE WHEN COALESCE(s.saldo_interno, 0) >= c.reserva_minima THEN 'OK' ELSE 'Alerta' END AS estado
                FROM treasury_cuentas c
                LEFT JOIN (
                    SELECT cuenta_id, MAX(fecha) AS fecha
                    FROM treasury_saldos_diarios
                    GROUP BY cuenta_id
                ) latest ON latest.cuenta_id = c.id
                LEFT JOIN treasury_saldos_diarios s
                    ON s.cuenta_id = latest.cuenta_id AND s.fecha = latest.fecha
                WHERE c.activa = TRUE
                ORDER BY c.nombre
                """,
                conn,
            )

    def balances_for_date(self, target_date: date) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                """
                SELECT s.id AS saldo_diario_id, c.nombre AS cuenta, c.moneda, s.fecha,
                       s.saldo_interno, s.saldo_extracto,
                       CASE WHEN s.saldo_extracto IS NULL THEN NULL ELSE s.saldo_interno - s.saldo_extracto END AS diferencia
                FROM treasury_saldos_diarios s
                JOIN treasury_cuentas c ON c.id = s.cuenta_id
                WHERE s.fecha = %s
                ORDER BY c.nombre
                """,
                conn,
                params=(target_date,),
            )

    def detect_discrepancies(self, target_date: date) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT IGNORE INTO treasury_discrepancias (saldo_diario_id, diferencia)
                    SELECT s.id, s.saldo_interno - s.saldo_extracto
                    FROM treasury_saldos_diarios s
                    WHERE s.fecha = %s
                      AND s.saldo_extracto IS NOT NULL
                      AND s.saldo_interno <> s.saldo_extracto
                      AND NOT EXISTS (
                          SELECT 1
                          FROM treasury_discrepancias d
                          WHERE d.saldo_diario_id = s.id AND d.estado = 'abierta'
                      )
                    """,
                    (target_date,),
                )
                return cur.rowcount or 0

    def open_discrepancies(self, target_date: date | None = None) -> pd.DataFrame:
        sql = """
            SELECT d.id, d.saldo_diario_id, d.diferencia, d.estado, d.detectada_en,
                   c.nombre AS cuenta, s.fecha
            FROM treasury_discrepancias d
            JOIN treasury_saldos_diarios s ON s.id = d.saldo_diario_id
            JOIN treasury_cuentas c ON c.id = s.cuenta_id
            WHERE d.estado = 'abierta'
        """
        params: tuple[Any, ...] = ()
        if target_date:
            sql += " AND s.fecha = %s"
            params = (target_date,)
        sql += " ORDER BY d.detectada_en DESC"
        with self._connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def register_action(self, discrepancy_id: int, descripcion: str, registrado_por: str | None = None) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO treasury_acciones_correctivas (discrepancia_id, descripcion, registrado_por)
                    VALUES (%s, %s, %s)
                    """,
                    (discrepancy_id, descripcion, registrado_por),
                )
                cur.execute("UPDATE treasury_discrepancias SET estado = 'cerrada' WHERE id = %s", (discrepancy_id,))

    def actions_for_date(self, target_date: date | None = None) -> pd.DataFrame:
        sql = """
            SELECT a.id, a.discrepancia_id, a.descripcion, a.registrado_por, a.registrado_en,
                   c.nombre AS cuenta, s.fecha, d.diferencia
            FROM treasury_acciones_correctivas a
            JOIN treasury_discrepancias d ON d.id = a.discrepancia_id
            JOIN treasury_saldos_diarios s ON s.id = d.saldo_diario_id
            JOIN treasury_cuentas c ON c.id = s.cuenta_id
        """
        params: tuple[Any, ...] = ()
        if target_date:
            sql += " WHERE s.fecha = %s"
            params = (target_date,)
        sql += " ORDER BY a.registrado_en DESC"
        with self._connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def period_data(self, start_date: date, end_date: date) -> tuple[pd.DataFrame, pd.DataFrame]:
        with self._connect() as conn:
            saldos = pd.read_sql_query(
                """
                SELECT s.*, c.nombre AS cuenta, c.moneda
                FROM treasury_saldos_diarios s
                JOIN treasury_cuentas c ON c.id = s.cuenta_id
                WHERE s.fecha BETWEEN %s AND %s
                ORDER BY s.fecha DESC, c.nombre
                """,
                conn,
                params=(start_date, end_date),
            )
        acciones = self.actions_for_date()
        if not acciones.empty:
            acciones = acciones[(acciones["fecha"] >= start_date) & (acciones["fecha"] <= end_date)]
        return saldos, acciones

    def save_report(self, start_date: date, end_date: date, modules: list[str], fmt: str, generado_por: str | None, filename: str, content: bytes) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO treasury_informes
                        (periodo_desde, periodo_hasta, modulos_incluidos, formato, generado_por, nombre_archivo, contenido)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (start_date, end_date, json.dumps(modules, ensure_ascii=False), fmt, generado_por, filename, content),
                )
                return int(cur.lastrowid)

    def recent_reports(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                "SELECT * FROM treasury_informes ORDER BY generado_en DESC LIMIT 20",
                conn,
            )

    def notes(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                "SELECT * FROM treasury_notas_coordinacion ORDER BY creado_en DESC LIMIT 100",
                conn,
            )

    def add_note(self, autor: str, area: str, mensaje: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO treasury_notas_coordinacion (autor, area, mensaje)
                    VALUES (%s, %s, %s)
                    """,
                    (autor, area, mensaje),
                )


def create_treasury_repository(store: MutableMapping[str, Any] | None = None):
    config = mysql_config_from_env()
    if config:
        return MySQLTreasuryRepository(config)
    return MemoryTreasuryRepository(store)
