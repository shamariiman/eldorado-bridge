import csv, io, os, json, paramiko, requests

SFTP_HOST = "52.27.75.88"
SFTP_USER = "vita49"
SFTP_PASS = "puls826"
CSV_PATH  = "/shipping_confirmations/shipping_confirmations.csv"

SHOP_URL = f"https://{os.environ['SHOPIFY_SHOP']}.myshopify.com"
HEADERS  = {
    "X-Shopify-Access-Token": os.environ["SHOP_TOKEN"],
    "Content-Type": "application/json"
}
LOCATION_ID = os.environ["LOCATION_ID"]

CARRIER_MAP = {
    "FHD":   "FedEx Ground",
    "F1DPR": "FedEx Standard Overnight",
    "U3DR":  "UPS 3 Day Select",
    "M01":   "USPS Ground Advantage"
}

def fetch_all_rows():
    """
    ① Try to open /shipping_confirmations/shipping_confirmations.csv
       (single rolling file).
    ② If that fails, read every *.csv in /shipping_confirmations/ folder.
    Returns a list of CSV.DictReader rows.
    """
    t = paramiko.Transport((SFTP_HOST, 22))
    t.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(t)

    rows = []
    try:
        raw = sftp.file("/shipping_confirmations/shipping_confirmations.csv").read().decode()
        rows.extend(csv.DictReader(io.StringIO(raw)))
    except IOError:
        for fname in sftp.listdir("/shipping_confirmations/"):
            if fname.endswith(".csv"):
                raw = sftp.file(f"/shipping_confirmations/{fname}").read().decode()
                rows.extend(csv.DictReader(io.StringIO(raw)))
    sftp.close(); t.close()
    return rows



def order_id_from_name(order_name):
    r = requests.get(
        f"{SHOP_URL}/admin/api/2025-07/orders.json",
        headers=HEADERS,
        params={"name": order_name}
    )
    orders = r.json().get("orders", [])
    return orders[0]["id"] if orders else None

def send_fulfillment(order_id, tracking, carrier):
    payload = {
        "fulfillment": {
            "location_id": LOCATION_ID,
            "tracking_number": tracking,
            "tracking_company": carrier,
            "notify_customer": True
        }
    }
    requests.post(
        f"{SHOP_URL}/admin/api/2025-07/orders/{order_id}/fulfillments.json",
        headers=HEADERS,
        json=payload
    )

def main():
    for row in fetch_all_rows():
        order_name = row["Supplier Order Number"]
        tracking   = row["Tracking Number"]
        carrier_cd = row["Carrier Method"]

        order_id = order_id_from_name(order_name)
        if not order_id:
            print(f"✗ {order_name} not found")
            continue

        send_fulfillment(
            order_id,
            tracking,
            CARRIER_MAP.get(carrier_cd, carrier_cd)
        )
        print(f"✓ {order_name} fulfilled – {tracking}")

if __name__ == "__main__":
    main()

