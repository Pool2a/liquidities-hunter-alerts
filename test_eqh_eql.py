
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

BASE_URL = "https://eea.okx.com"

MARKETS = {
    "BTC": "BTC",
    "ETH": "ETH",
    "OR": "XAU"
}

TIMEFRAMES = {
    "M15": "15m",
    "H1": "1H",
    "H4": "4H",
    "D1": "1D",
    "W1": "1W"
}

PIVOT_LEN = 5
ATR_LEN = 14
EQ_ATR = 0.20
LIMIT = 300


def api_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LiquiditiesHunter/1.0"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def find_contracts():
    found = {}

    for inst_type in ["FUTURES", "SWAP"]:
        result = api_get(
            "/api/v5/public/instruments",
            {"instType": inst_type}
        )

        if result.get("code") != "0":
            print("Erreur instruments :", result.get("msg"))
            continue

        for instrument in result.get("data", []):
            inst_id = instrument.get("instId", "")

            if instrument.get("state") != "live":
                continue

            upper_id = inst_id.upper()

            if "XPERP" not in upper_id:
                continue

            for symbol, keyword in MARKETS.items():
                if keyword not in upper_id:
                    continue

                if symbol == "ETH" and "ETHFI" in upper_id:
                    continue

                item = (inst_type, inst_id)

                if symbol not in found:
                    found[symbol] = item

    return found


def get_candles(inst_id, bar):
    result = api_get(
        "/api/v5/market/candles",
        {
            "instId": inst_id,
            "bar": bar,
            "limit": str(LIMIT)
        }
    )

    if result.get("code") != "0":
        raise RuntimeError(result.get("msg", "Erreur OKX"))

    candles = []

    for row in result.get("data", []):
        if row[8] != "1":
            continue

        candles.append({
            "time": int(row[0]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4])
        })

    candles.sort(key=lambda candle: candle["time"])
    return candles


def calculate_atr(candles):
    tr_values = []
    atr_values = [None] * len(candles)

    for i, candle in enumerate(candles):
        high = candle["high"]
        low = candle["low"]

        if i == 0:
            tr = high - low
        else:
            previous_close = candles[i - 1]["close"]

            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close)
            )

        tr_values.append(tr)

    if len(tr_values) < ATR_LEN:
        return atr_values

    atr = sum(tr_values[:ATR_LEN]) / ATR_LEN
    atr_values[ATR_LEN - 1] = atr

    for i in range(ATR_LEN, len(tr_values)):
        atr = (
            (atr * (ATR_LEN - 1)) + tr_values[i]
        ) / ATR_LEN

        atr_values[i] = atr

    return atr_values


def detect_pivots(candles, atr_values, is_high):
    pivots = []
    length = len(candles)

    for i in range(PIVOT_LEN, length - PIVOT_LEN):

        if is_high:
            price = candles[i]["high"]

            left = [
                c["high"]
                for c in candles[i-PIVOT_LEN:i]
            ]

            right = [
                c["high"]
                for c in candles[i+1:i+PIVOT_LEN+1]
            ]

            valid = price >= max(left) and price > max(right)

        else:
            price = candles[i]["low"]

            left = [
                c["low"]
                for c in candles[i-PIVOT_LEN:i]
            ]

            right = [
                c["low"]
                for c in candles[i+1:i+PIVOT_LEN+1]
            ]

            valid = price <= min(left) and price < min(right)

        if valid:
            pivots.append({
                "index": i,
                "price": price,
                "atr": atr_values[i],
                "time": candles[i]["time"]
            })

    return pivots


def detect_equal_levels(pivots):
    signals = []
    previous = None

    for pivot in pivots:

        if previous is not None:
            current_atr = pivot["atr"]
            previous_atr = previous["atr"]

            if current_atr is not None and previous_atr is not None:

                tolerance = (
                    (current_atr + previous_atr) / 2
                ) * EQ_ATR

                difference = abs(
                    pivot["price"] - previous["price"]
                )

                if difference <= tolerance:
                    signals.append(pivot)

        previous = pivot

    return signals


def display_levels(title, signals):

    print("\n" + title)

    if not signals:
        print("Aucun niveau détecté")
        return

    for number, signal in enumerate(signals, start=1):

        date = datetime.fromtimestamp(
            signal["time"] / 1000,
            timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")

        print(
            number,
            "| Prix :",
            signal["price"],
            "| Date :",
            date
        )


def main():
    print("================================")
    print(" LIQUIDITIES HUNTER - EQH/EQL")
    print("================================")

    contracts = find_contracts()

    print("\n=== CONTROLE DES CONTRATS ===")

    for symbol in MARKETS:

        if symbol in contracts:
            inst_type, inst_id = contracts[symbol]

            print(
                symbol,
                "-",
                inst_type,
                "-",
                inst_id
            )
        else:
            print("CONTRAT INTROUVABLE :", symbol)

    print("\n=== ANALYSE EQH / EQL ===")

    for symbol in MARKETS:

        if symbol not in contracts:
            continue

        inst_type, inst_id = contracts[symbol]

        print("\n================================")
        print("MARCHE :", symbol)
        print("CONTRAT :", inst_id)
        print("================================")

        for timeframe, bar in TIMEFRAMES.items():

            print("\n---", timeframe, "---")

            try:
                candles = get_candles(inst_id, bar)

                print("Bougies utilisees :", len(candles))

                if len(candles) < 2 * PIVOT_LEN + ATR_LEN:
                    print(
                        "Historique insuffisant :",
                        len(candles)
                    )
                    continue

                atr_values = calculate_atr(candles)

                high_pivots = detect_pivots(
                    candles, atr_values, True
                )

                low_pivots = detect_pivots(
                    candles, atr_values, False
                )

                eqh = detect_equal_levels(high_pivots)
                eql = detect_equal_levels(low_pivots)

                print("Pivots hauts :", len(high_pivots))
                print("Pivots bas :", len(low_pivots))
                print("EQH detectes :", len(eqh))
                print("EQL detectes :", len(eql))

                display_levels("DETAIL DES EQH :", eqh)
                display_levels("DETAIL DES EQL :", eql)

            except Exception as error:
                print("ERREUR :", error)

    print("\n========== FIN DU TEST ==========")


if __name__ == "__main__":
    main()
