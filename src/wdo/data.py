"""Carga, validação e construção da série M5 (timestamps em America/Sao_Paulo)."""
from __future__ import annotations

from pathlib import Path
import io
import json
import urllib.request

import pandas as pd

REQUIRED_COLUMNS = ["datetime", "open", "high", "low", "close", "volume"]


def _as_brasilia(values: pd.Series, timezone: str) -> pd.Series:
    timestamps = pd.to_datetime(values, errors="raise")
    if timestamps.dt.tz is None:
        return timestamps.dt.tz_localize(timezone, ambiguous="raise", nonexistent="raise")
    return timestamps.dt.tz_convert(timezone)


def validate_bars(bars: pd.DataFrame, timezone: str = "America/Sao_Paulo") -> pd.DataFrame:
    missing = sorted(set(REQUIRED_COLUMNS).difference(bars.columns))
    if missing:
        raise ValueError(f"Dados sem colunas obrigatórias: {missing}")
    data = bars.copy()
    data["datetime"] = _as_brasilia(data["datetime"], timezone)
    data = data.sort_values("datetime").reset_index(drop=True)
    if data["datetime"].duplicated().any():
        raise ValueError("Há timestamps M5 duplicados.")
    for column in ["open", "high", "low", "close", "volume"]:
        data[column] = pd.to_numeric(data[column], errors="raise")
    invalid = (data["high"] < data[["open", "close", "low"]].max(axis=1)) | (data["low"] > data[["open", "close", "high"]].min(axis=1))
    if invalid.any():
        raise ValueError(f"OHLC inválido em {int(invalid.sum())} barra(s).")
    gaps = data["datetime"].diff().dt.total_seconds().div(60)
    intraday_gaps = gaps[(gaps > 5) & (gaps < 60)]
    if not intraday_gaps.empty:
        raise ValueError("Há lacunas intradiárias de 5 a 60 minutos; corrija a fonte antes do backtest.")
    return data


def load_csv_or_parquet(path: str | Path, timezone: str = "America/Sao_Paulo") -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    elif path.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    else:
        raise ValueError("Use CSV, Parquet ou PQ.")
    return validate_bars(frame, timezone)


def load_mt5_export(path: str | Path, timezone: str = "America/Sao_Paulo", volume_column: str = "VOL") -> pd.DataFrame:
    """Lê exportação do MT5 (TAB, colunas <DATE> <TIME> <OPEN>...) e devolve OHLCV validado.

    `volume_column` escolhe entre VOL (volume real) e TICKVOL (contagem de ticks).
    """
    # Este export vem com cada linha inteira entre aspas ("a<TAB>b<TAB>c"); remove-as antes do parse.
    with open(path, encoding="utf-8-sig") as handle:
        lines = [line.strip().strip('"') for line in handle if line.strip()]
    frame = pd.read_csv(io.StringIO("\n".join(lines)), sep="\t")
    frame.columns = [str(c).strip().strip('"').strip("<>").upper() for c in frame.columns]
    required = {"DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE", volume_column}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Exportação MT5 sem colunas: {missing}")
    out = pd.DataFrame({
        "datetime": pd.to_datetime(frame["DATE"].astype(str) + " " + frame["TIME"].astype(str), format="%Y.%m.%d %H:%M:%S"),
        "open": frame["OPEN"], "high": frame["HIGH"], "low": frame["LOW"], "close": frame["CLOSE"],
        "volume": frame[volume_column],
    })
    return validate_bars(out, timezone)


def load_http_ohlcv(url: str, timezone: str = "America/Sao_Paulo", timeout: int = 30) -> pd.DataFrame:
    """Adaptador deliberadamente genérico; endpoint deve retornar lista JSON OHLCV M5."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    frame = pd.DataFrame(payload["data"] if isinstance(payload, dict) and "data" in payload else payload)
    data = validate_bars(frame, timezone)
    if len(data) > 1 and not (data["datetime"].diff().dt.total_seconds().dropna() == 300).any():
        raise ValueError("API não comprovou granularidade M5; use CSV/Parquet.")
    return data


def build_continuous_contract(raw: pd.DataFrame, rollover: pd.DataFrame, start: str, end: str, timezone: str) -> pd.DataFrame:
    """Monta série somente com calendário explícito: contract, start, end."""
    required = {"contract", "start", "end"}
    if not required.issubset(rollover.columns) or "contract" not in raw.columns:
        raise ValueError("Rollover requer contract/start/end e os candles requerem contract.")
    schedule = rollover.copy()
    schedule["start"] = _as_brasilia(schedule["start"], timezone)
    schedule["end"] = _as_brasilia(schedule["end"], timezone)
    schedule = schedule.sort_values("start")
    if (schedule["end"] < schedule["start"]).any() or (schedule["start"].iloc[1:].reset_index(drop=True) <= schedule["end"].iloc[:-1].reset_index(drop=True)).any():
        raise ValueError("Tabela de rollover possui intervalo inválido ou sobreposto.")
    data = raw.copy(); data["datetime"] = _as_brasilia(data["datetime"], timezone)
    pieces = []
    for row in schedule.itertuples(index=False):
        selected = data[(data.contract == row.contract) & (data.datetime >= row.start) & (data.datetime <= row.end)]
        pieces.append(selected)
    result = validate_bars(pd.concat(pieces, ignore_index=True), timezone)
    start_ts, end_ts = pd.Timestamp(start, tz=timezone), pd.Timestamp(end, tz=timezone) + pd.Timedelta(days=1) - pd.Timedelta(minutes=5)
    result = result[(result.datetime >= start_ts) & (result.datetime <= end_ts)].copy()
    if result.empty:
        raise ValueError("Rollover não cobriu o período solicitado.")
    return result
