import csv, io, os, json, paramiko, requests

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

def sku_to_item_id(sku):
    q = """
    { productVariants(first:1, query:"sku:%s") {
        nodes { inventoryItem { id } }
      } }
    """ % sku
    r = requests.post(f"{SHOP_URL}/admin/api/2025-07/graphql.json",
                      headers=HEADERS, json={"query": q})
    data = json.loads(r.text)
    item = data["data"]["productVariants"]["nodes"]
    return item[0]["inventoryItem"]["id"] if item else None

def set_quantity(item_id, qty):
    payload = {
        "location_id": LOCATION_ID,
        "inventory_item_id": item_id.split("/")[-1],
        "available": int(qty)
    }
    requests.post(f"{SHOP_URL}/admin/api/2025-07/inventory_levels/set.json",
                  headers=HEADERS, json=payload)

def main():
    feed = csv.DictReader(io.StringIO(fetch_feed()), delimiter=',')
    for row in feed:
        sku = row["Model"]
        qty = row["quantity"]
        item_id = sku_to_item_id(sku)
        if item_id:
            set_quantity(item_id, qty)

if __name__ == "__main__":
    main()
