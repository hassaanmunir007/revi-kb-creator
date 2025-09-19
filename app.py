import streamlit as st
import json
import csv
import io
import requests

st.set_page_config(page_title="JSON → CSV (Menu)", page_icon="📄")

st.title("JSON → CSV Converter (Menu)")
st.caption("Upload a JSON file or provide a URL returning JSON. Outputs a CSV based on the menu schema.")

# --- This mirrors your original transformation logic ---
# Source structure: data["menu"] is expected to be a dict of items
# Each item may have: name, description, id, price, category
HEADERS = ["name", "description", "id", "price", "category"]

def json_to_csv_bytes(data: dict) -> bytes:
    """
    Convert JSON to CSV using the exact logic of your script:
      - Read data["menu"]
      - Iterate values (when dict) / items (when list)
      - Write only the fields: name, description, id, price, category
    Returns CSV as UTF-8 bytes.
    """
    menu_data = data.get("menu", {})

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()

    def write_row(item: dict):
        row = {key: item.get(key, "") for key in HEADERS}
        writer.writerow(row)

    if isinstance(menu_data, dict):
        for item in menu_data.values():
            if isinstance(item, dict):
                write_row(item)
    elif isinstance(menu_data, list):
        for item in menu_data:
            if isinstance(item, dict):
                write_row(item)
    else:
        # If menu is missing or of unexpected type, just write header (empty CSV)
        pass

    # Return bytes (no BOM); Excel generally handles UTF-8 now, but add BOM if you prefer.
    return output.getvalue().encode("utf-8")


# ---- UI: Input mode ----
mode = st.radio("Choose input method:", ["Upload JSON file", "Fetch from URL"], horizontal=True)

json_data = None

if mode == "Upload JSON file":
    uploaded = st.file_uploader("Upload a .json file", type=["json"])
    if uploaded is not None:
        try:
            json_text = uploaded.read().decode("utf-8")
            json_data = json.loads(json_text)
            st.success("JSON parsed successfully from file.")
        except Exception as e:
            st.error(f"Failed to parse JSON file: {e}")

else:
    url = st.text_input("Enter a URL that returns JSON (HTTPS recommended):", placeholder="https://example.com/menu.json")
    fetch = st.button("Fetch JSON")
    if fetch and url:
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            json_data = resp.json()
            st.success("JSON fetched and parsed successfully from URL.")
        except Exception as e:
            st.error(f"Failed to fetch/parse JSON: {e}")

# ---- Process & Download ----
if json_data is not None:
    # Preview: show what we’ll convert
    with st.expander("Preview detected JSON keys and menu size", expanded=False):
        st.write("Top-level keys:", list(json_data.keys()))
        menu = json_data.get("menu")
        if isinstance(menu, dict):
            st.write(f"`menu` type: dict — items: {len(menu)}")
        elif isinstance(menu, list):
            st.write(f"`menu` type: list — items: {len(menu)}")
        else:
            st.write(f"`menu` type: {type(menu).__name__} (not iterable)")

    csv_bytes = json_to_csv_bytes(json_data)

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_bytes,
        file_name="output.csv",
        mime="text/csv",
    )

    # Optional quick peek (first 2 KB) for reassurance
    with st.expander("Peek at CSV (first few lines)"):
        peek = csv_bytes.decode("utf-8")[:2048]
        st.code(peek, language="csv")
else:
    st.info("Provide a JSON file or URL to begin.")
