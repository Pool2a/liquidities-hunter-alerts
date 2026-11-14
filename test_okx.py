
import json
import urllib.request
import urllib.parse

BASE_URL = "https://eea.okx.com"

MARKETS = {
    "BTC": "BTC",
    "ETH": "ETH",
    "OR": "XAU"
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

print("=== LIQUIDITIES HUNTER : TEST OKX ===")

found = []

for inst_type in ["FUTURES", "SWAP"]:
    print(f"\nRecherche dans {inst_type}...")

    try:
        result = api_get(
            "/api/v5/public/instruments",
            {"instType": inst_type}
        )

        if result.get("code") != "0":
            print("Erreur API :", result.get("msg"))
            continue

        for instrument in result.get("data", []):
            inst_id = instrument.get("instId", "")
            state = instrument.get("state", "")

            if state != "live":
                continue

            upper_id = inst_id.upper()

            for symbol, keyword in MARKETS.items():
                if keyword in upper_id and (
                    "XPERP" in upper_id or "X-PERP" in upper_id
                ):
                    found.append((symbol, inst_type, inst_id))
                    print(f"{symbol} : {inst_id}")

    except Exception as error:
        print("Erreur :", error)

print("\n=== TEST DES BOUGIES M15 ===")

if not found:
    print("Aucun contrat X-Perp trouvé.")
    print("Il faudra vérifier les identifiants avec une autre requête.")
else:
    for symbol, inst_type, inst_id in found:
        try:
            result = api_get(
                "/api/v5/market/candles",
                {
                    "instId": inst_id,
                    "bar": "15m",
                    "limit": "2"
                }
            )

            data = result.get("data", [])

            if result.get("code") == "0" and data:
                candle = data[0]
                print(
                    f"OK - {symbol} - {inst_id} "
                    f"- Dernière clôture : {candle[4]}"
                )
            else:
                print(f"ECHEC - {inst_id} : {result.get('msg')}")

        except Exception as error:
            print(f"ERREUR - {inst_id} : {error}")

print("\n=== FIN DU TEST ===")

