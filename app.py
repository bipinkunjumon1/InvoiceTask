import os
import fitz  # PyMuPDF
import pdfplumber
import io
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import json
import streamlit as st

# --- Configuration ---
load_dotenv()

# Load API key from environment variables
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    st.error("FATAL: GOOGLE_API_KEY environment variable not set. Please set it to your Gemini API key.")
    st.stop()

# --- Prompts ---
TEXT_PROMPT = """
You are an expert accounts payable specialist. Your task is to analyze the following text content from an invoice and a purchase order and extract key information.

From the INVOICE text, extract:
- Invoice Number
- Date
- Vendor Name
- A list of all line items. Each item should have a 'description', 'quantity', and 'price'.
- Total Amount

From the PURCHASE ORDER text, extract:
- PO Number
- Date
- Vendor Name
- A list of all ordered items. Each item should have a 'description', 'quantity', and 'price'.
- Total Amount

Return your findings ONLY as a single, minified JSON object. The JSON structure must be:
{
  "invoice_data": {
    "invoice_no": "...", "date": "...", "vendor": "...",
    "items": [{"description": "...", "quantity": 1, "price": 0.00}],
    "total": 0.00
  },
  "po_data": {
    "po_no": "...", "date": "...", "vendor": "...",
    "items": [{"description": "...", "quantity": 1, "price": 0.00}],
    "total": 0.00
  }
}
"""

IMAGE_PROMPT = """
You are an expert accounts payable specialist. Your task is to extract key information from the provided document images.

From the INVOICE image, extract:
- Invoice Number
- Date
- Vendor Name
- A list of all line items. Each item should have a 'description', 'quantity', and 'price'.
- Total Amount

From the PURCHASE ORDER image, extract:
- PO Number
- Date
- Vendor Name
- A list of all ordered items. Each item should have a 'description', 'quantity', and 'price'.
- Total Amount

Return your findings ONLY as a single, minified JSON object. The JSON structure must be:
{
  "invoice_data": {
    "invoice_no": "...", "date": "...", "vendor": "...",
    "items": [{"description": "...", "quantity": 1, "price": 0.00}],
    "total": 0.00
  },
  "po_data": {
    "po_no": "...", "date": "...", "vendor": "...",
    "items": [{"description": "...", "quantity": 1, "price": 0.00}],
    "total": 0.00
  }
}
"""

# --- Gemini API Interaction ---
def get_gemini_response(payload):
    model = genai.GenerativeModel('models/gemini-pro-latest')
    try:
        generation_config = genai.types.GenerationConfig(temperature=0)
        response = model.generate_content(payload, generation_config=generation_config)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_text)
    except Exception as e:
        st.error("An error occurred with the Gemini API or its response.")
        st.write("Raw Gemini response:", response.text if 'response' in locals() else "No response object")
        st.stop()

# --- Helpers ---
def get_text_with_pdfplumber(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return text.strip()
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        return ""

def prepare_image(file_path):
    if not file_path.lower().endswith('.pdf'):
        return Image.open(file_path)
    try:
        doc = fitz.open(file_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        doc.close()
        return Image.open(io.BytesIO(img_data))
    except Exception as e:
        st.error(f"Failed to convert PDF to image: {e}")
        st.stop()

# --- Streamlit UI ---
st.set_page_config(page_title="Invoice & PO Matching Tool", layout="wide")

# Custom CSS with Tailwind CDN
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<style>
    .card { background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding: 20px; margin-bottom: 20px; }
    .header { background-color: #1f2937; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
    .sidebar-card { background-color: #f9fafb; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    .btn-primary { background-color: #2563eb; color: white; padding: 10px 20px; border-radius: 6px; }
    .btn-primary:hover { background-color: #1d4ed8; }
    .table-header { background-color: #ffffff; color: #000000; font-weight: 600; }
    .status-approved { color: #15803d; font-weight: bold; }
    .status-review { color: #b91c1c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header">
    <div class="flex items-center">
        <h1 class="text-2xl font-bold">📑 Invoice & PO Matching Tool</h1>
    </div>
    <p class="mt-2 text-sm">Upload an Invoice and Purchase Order to automatically compare and verify their details.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for uploads and actions
with st.sidebar:
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.subheader("Upload Documents")
    invoice_file = st.file_uploader("📄 Invoice", type=["pdf", "png", "jpg", "jpeg"], key="invoice")
    po_file = st.file_uploader("📑 Purchase Order", type=["pdf", "png", "jpg", "jpeg"], key="po")
    if st.button("🔍 Compare Documents", key="compare", help="Click to analyze the uploaded documents"):
        if invoice_file is None or po_file is None:
            st.error("Please upload both an Invoice and a Purchase Order file.")
            st.stop()

        # Save temp files
        invoice_path = f"temp_invoice_{invoice_file.name}"
        po_path = f"temp_po_{po_file.name}"
        with open(invoice_path, "wb") as f:
            f.write(invoice_file.read())
        with open(po_path, "wb") as f:
            f.write(po_file.read())

        invoice_text = get_text_with_pdfplumber(invoice_path)
        po_text = get_text_with_pdfplumber(po_path)

        if invoice_text and po_text:
            st.info("✅ Using text-based extraction.")
            payload = [TEXT_PROMPT, f"\n--- INVOICE TEXT ---\n{invoice_text}", f"\n--- PO TEXT ---\n{po_text}"]
            analysis = get_gemini_response(payload)
        else:
            st.warning("⚠️ Text extraction failed. Falling back to image-based analysis.")
            invoice_image = prepare_image(invoice_path)
            po_image = prepare_image(po_path)
            payload = [IMAGE_PROMPT, invoice_image, po_image]
            analysis = get_gemini_response(payload)

        invoice_data = analysis.get('invoice_data', {})
        po_data = analysis.get('po_data', {})
    st.markdown('</div>', unsafe_allow_html=True)

# Main content
if 'analysis' in locals():
    col1, col2 = st.columns(2)

    def display_doc(title, data, doc_type):
        st.markdown(f'<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<h2 class="text-xl font-semibold">{title}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p><strong>{doc_type.capitalize()} #:</strong> {data.get(f"{doc_type.lower()}_no", "N/A")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p><strong>Date:</strong> {data.get("date", "N/A")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p><strong>Vendor:</strong> {data.get("vendor", "N/A")}</p>', unsafe_allow_html=True)
        st.markdown('<h3 class="text-lg font-medium mt-4">Items</h3>', unsafe_allow_html=True)
        items = data.get("items", [])
        if items:
            # Custom table styling
            table_html = '<table class="w-full border-collapse"><thead><tr class="table-header">'
            table_html += '<th class="p-2 text-left">Description</th><th class="p-2 text-left">Quantity</th><th class="p-2 text-left">Price</th></tr></thead><tbody>'
            for item in items:
                table_html += f'<tr><td class="p-2 border-t">{item.get("description", "N/A")}</td>'
                table_html += f'<td class="p-2 border-t">{item.get("quantity", "N/A")}</td>'
                table_html += f'<td class="p-2 border-t">${float(item.get("price", 0.0)):.2f}</td></tr>'
            table_html += '</tbody></table>'
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.markdown('<p class="text-gray-500">No items found.</p>', unsafe_allow_html=True)
        st.markdown(f'<h3 class="text-lg font-medium mt-4">Total: ${float(data.get("total", 0.0)):.2f}</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col1:
        display_doc("📄 Invoice Details", invoice_data, "invoice")
    with col2:
        display_doc("📑 Purchase Order Details", po_data, "po")

    # --- Match/Mismatch Summary ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2 class="text-xl font-semibold">🔎 Match/Mismatch Summary</h2>', unsafe_allow_html=True)

    def generate_match_summary(invoice_data, po_data):
        lines = []
        issues = []

        invoice_no = invoice_data.get("invoice_no", "N/A")
        po_no = po_data.get("po_no", "N/A")
        lines.append(f"• Invoice #{invoice_no} matches PO #{po_no}")

        # Vendor check
        if invoice_data.get("vendor") == po_data.get("vendor"):
            lines.append(f"• Vendor matches: {invoice_data.get('vendor')} ✓")
        else:
            lines.append(f"• Vendor mismatch: Invoice ({invoice_data.get('vendor')}) vs PO ({po_data.get('vendor')}) ✗")
            issues.append("Vendor mismatch")

        # Total check
        invoice_total = float(invoice_data.get("total", 0.0))
        po_total = float(po_data.get("total", 0.0))
        if abs(invoice_total - po_total) < 0.01:
            lines.append(f"• Total amount matches: ${invoice_total:.2f} ✓")
        else:
            diff = abs(invoice_total - po_total)
            lines.append(f"• Total amount mismatch: Invoice (${invoice_total:.2f}) vs PO (${po_total:.2f}) ✗")
            lines.append(f"→ Difference: ${diff:.2f}")
            issues.append("Total mismatch")

        # Items check
        invoice_items = invoice_data.get("items", [])
        po_items = po_data.get("items", [])

        all_items_match = True
        if len(invoice_items) != len(po_items):
            all_items_match = False
        else:
            for i_item, p_item in zip(invoice_items, po_items):
                if (
                    i_item.get("description") != p_item.get("description") or
                    float(i_item.get("price",0)) != float(p_item.get("price",0)) or
                    int(i_item.get("quantity",0)) != int(p_item.get("quantity",0))
                ):
                    all_items_match = False
                    break

        if all_items_match:
            lines.append("• All items match ✓")
        else:
            lines.append("• Items mismatch ✗")
            issues.append("Items mismatch")

        # Status
        if not issues:
            lines.append('<span class="status-approved">→ Status: APPROVED - No issues found! ✅</span>')
        else:
            lines.append('<span class="status-review">→ Status: NEEDS REVIEW ⚠️ - Please check the highlighted discrepancies!</span>')
        
        summary = "<br>".join(lines)
        return summary

    match_summary = generate_match_summary(invoice_data, po_data)
    st.markdown(match_summary, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)