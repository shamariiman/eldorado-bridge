import csv, io, os, json, paramiko, requests
def fetch_shop_skus():
    """
    Get every SKU you have in Shopify, map → numeric inventory_item_id.
    """
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


SFTP_HOST = "52.27.75.88"
SFTP_USER = "vita49"
SFTP_PASS = "puls826"
CSV_PATH  = "/feeds/inventory_cga0a.csv"


SHOP_URL  = f"https://{os.environ['SHOPIFY_SHOP']}.myshopify.com"
HEADERS   = {
    "X-Shopify-Access-Token": os.environ["SHOP_TOKEN"],
    "Content-Type": "application/json"
}
LOCATION_ID = os.environ["LOCATION_ID"]

def fetch_feed():
    t = paramiko.Transport((SFTP_HOST, 22))
    t.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(t)
    raw = sftp.file(CSV_PATH).read().decode()
    sftp.close()
    t.close()
    return raw


def set_qty(item_id, qty):
    """
    Push the new quantity to Shopify’s inventory_levels/set endpoint.
    `item_id` is the integer inventory_item_id (not the variant id).
    """
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



def main():
    shop_skus = fetch_shop_skus()

    feed = csv.DictReader(io.StringIO(fetch_feed()), delimiter=',')

    for row in feed:
        sku = row["Model"]
        if sku not in shop_skus:
            continue        

        item_id = shop_skus[sku]
        qty     = row["quantity"]

        set_qty(item_id, qty)
        print(f"✓ {sku} → set {qty}")



if __name__ == "__main__":
    main()




