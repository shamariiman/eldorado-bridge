from flask import Flask, request
import paramiko

SHOPIFY_SHARED_SECRET = "put_your_webhook_secret_here"
SFTP_HOST = "52.27.75.88"
SFTP_USER = "vita49"
SFTP_PASS = "puls826"
ACCOUNT_ID = "49826PF"
SHIP_VIA = "FHD"

app = Flask(__name__)

def build_xml(order):
    a = order["shipping_address"]
    x = f"""<AccountId>{ACCOUNT_ID}</AccountId>
<Name>{a['name']}</Name>
<AddressLine1>{a['address1']}</AddressLine1>
<City>{a['city']}</City>
<StateCode>{a['province_code']}</StateCode>
<ZipCode>{a['zip']}</ZipCode>
<CountryCode>{a['country_code']}</CountryCode>
<PhoneNumber>{a.get('phone','0000000000').replace('-','')}</PhoneNumber>
<ShipVia>{SHIP_VIA}</ShipVia>
<SourceOrderNumber>{order['name']}</SourceOrderNumber>
<signatureRequired>N</signatureRequired>
<Products>"""
    for i in order["line_items"]:
        x += f"""
  <Product><Code>{i['sku']}</Code><Quantity>{i['quantity']}</Quantity></Product>"""
    x += "\n</Products>"
    return x

def upload(txt, name):
    t = paramiko.Transport((SFTP_HOST, 22))
    t.connect(username=SFTP_USER, password=SFTP_PASS)
    s = paramiko.SFTPClient.from_transport(t)
    f = f"/uploads/Order-{name.replace('#','')}.xml"
    with s.file(f, "w") as h:
        h.write(txt)
    s.close()
    t.close()

@app.route("/hook", methods=["POST"])
def hook():
    d = request.get_json()
    order = d.get("order", d)          # works for test and real payloads
    xml_payload = build_xml(order)
    upload(xml_payload, order["name"])
    return "ok"

if __name__ == "__main__":
    import os; app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
