
import json
import urllib.request
import urllib.parse

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

def api_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LiquiditiesHunter/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

print("=== LIQUIDITIES HUNTER : TEST MULTI-TF OKX ===")

found = []

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

        for symbol, keyword in MARKETS.items():
            if keyword in upper_id and "XPERP" in upper_id:
                item = (symbol, inst_type, inst_id)
                if item not in found:
                    found.append(item)

print("\n=== CONTRATS TROUVES ===")
for symbol, inst_type, inst_id in found:
    print(symbol, "-", inst_id)

print("\n=== TEST DES BOUGIES ===")

for symbol, inst_type, inst_id in found:
    print(f"\n--- {symbol} : {inst_id} ---")

    for label, bar in TIMEFRAMES.items():
        try:
            result = api_get(
                "/api/v5/market/candles",
                {
                    "instId": inst_id,
                    "bar": bar,
                    "limit": "2"
                }
            )

            data = result.get("data", [])

            if result.get("code") == "0" and data:
                print(f"OK - {label} - Cloture : {data[0][4]}")
            else:
                print(f"ECHEC - {label} - {result.get('msg')}")

        except Exception as error:
            print(f"ERREUR - {label} - {error}")

print("\n=== FIN DU TEST ===")
