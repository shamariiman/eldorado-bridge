import csv, io, json, paramiko, requests

# --- Your Shopify + Eldorado Info ---
SFTP_HOST = "52.27.75.88"
SFTP_USER = "vita49"
SFTP_PASS = "puls826"
CSV_PATH  = "/feeds/inventory_cga0a.csv"

SHOP_URL  = "https://loveboxllc.myshopify.com"
HEADERS   = {
    "X-Shopify-Access-Token": "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",
    "Content-Type": "application/json"
}

LOCATION_ID = "65228243002"  # Eldorado location
print("📍 Location ID being used:", LOCATION_ID)

# --- Grab SKU + inventory item IDs from Shopify ---
def fetch_shop_skus():
    skus = {}
    cursor = None

    while True:
        after = f', after: "{cursor}"' if cursor else ''
        query = f'''
        {{
          shop {{
            productVariants(first:250{after}) {{
              edges {{
                node {{
                  sku
                  inventoryItem {{ id }}
                }}
              }}
              pageInfo {{ hasNextPage endCursor }}
            }}
          }}
        }}'''
        resp = requests.post(
            f"{SHOP_URL}/admin/api/2025-07/graphql.json",
            headers=HEADERS,
            json={"query": query}
        )
        data = resp.json()["data"]["shop"]["productVariants"]
        for edge in data["edges"]:
            node = edge["node"]
            gid = node["inventoryItem"]["id"]
            numeric_id = gid.split("/")[-1]
            skus[node["sku"]] = numeric_id
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]

    return skus

# --- Pull inventory CSV from Eldorado ---
def fetch_feed():
    t = paramiko.Transport((SFTP_HOST, 22))
    t.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    raw = sftp.file(CSV_PATH).read().decode()
    sftp.close()
    t.close()
    return raw

# --- Push quantity to Shopify ---
def set_qty(item_id, qty):
    payload = {
        "location_id": LOCATION_ID,
        "inventory_item_id": item_id,
        "available": int(qty)
    }
    requests.post(
        f"{SHOP_URL}/admin/api/2025-07/inventory_levels/set.json",
        headers=HEADERS,
        json=payload
    )

# --- Run it all ---
def main():
    shop_skus = fetch_shop_skus()
    feed = csv.DictReader(io.StringIO(fetch_feed()), delimiter=',')

    for row in feed:
        sku = row["Model"]
        if sku not in shop_skus:
            print(f"⚠️ SKU not found in Shopify: {sku}")
            continue

        item_id = shop_skus[sku]
        qty     = row["quantity"]

        set_qty(item_id, qty)
        print(f"✅ {sku} → set {qty} units at location {LOCATION_ID} (🆔 inventory_item_id: {item_id})")

if __name__ == "__main__":
    main()


