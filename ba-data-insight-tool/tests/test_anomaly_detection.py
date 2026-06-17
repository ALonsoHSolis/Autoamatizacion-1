import pandas as pd

from src.anomaly_detection import detect_anomalies


def test_detect_anomalies_with_z_score():
    df = pd.DataFrame({"monto": [100, 102, 98, 101, 500]})
    anomalies = detect_anomalies(df, "monto", threshold=1.5)
    assert not anomalies.empty
    assert anomalies.iloc[0]["valor_analizado"] == 500
    assert "limite_superior" in anomalies.columns
    assert anomalies.iloc[0]["tipo_desvio"] == "Sobre el rango esperado"
