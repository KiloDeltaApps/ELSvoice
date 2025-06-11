import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import re
from fpdf import FPDF
import base64
from io import BytesIO

# Initialize session state
if 'invoice_lines' not in st.session_state:
    st.session_state.invoice_lines = []
if 'invoice_number' not in st.session_state:
    st.session_state.invoice_number = 1
if 'payment_terms_days' not in st.session_state:
    st.session_state.payment_terms_days = 14
if 'language' not in st.session_state:
    st.session_state.language = 'nl'
if 'description' not in st.session_state:
    st.session_state.description = "Invoice for ice skating activities at DSSV ELS."
if 'show_download' not in st.session_state:
    st.session_state.show_download = False
if 'current_pdf' not in st.session_state:
    st.session_state.current_pdf = None
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

# Translations
translations = {
    'nl': {
        'invoice': 'FACTUUR',
        'invoice_number': 'Factuurnummer',
        'date': 'Datum',
        'customer': 'Ontvanger',
        'due_date': 'Vervaldatum',
        'description': 'Omschrijving',
        'quantity': 'Aantal',
        'price': 'Prijs',
        'amount': 'Bedrag',
        'total': 'Totaal',
        'payment_instructions': 'Gelieve binnen de termijn over te maken op NL51 ABNA 0552 4048 45 t.n.v DSSV ELS en onder vermelding van het factuurnummer'
    },
    'en': {
        'invoice': 'INVOICE',
        'invoice_number': 'Invoice #',
        'date': 'Date',
        'customer': 'Recipient',
        'due_date': 'Due Date',
        'description': 'Description',
        'quantity': 'Quantity',
        'price': 'Price',
        'amount': 'Amount',
        'total': 'Total',
        'payment_instructions': 'Please transfer the amount within the payment term to NL51 ABNA 0552 4048 45 in name of DSSV ELS, stating the invoice number'
    }
}

def generate_pdf(customer_name, invoice_name):
    pdf = FPDF()
    pdf.add_page('P', 'A4')

    trans = translations[st.session_state.language]
    invoice_date = datetime.now()
    payment_due_date = invoice_date + pd.Timedelta(days=st.session_state.payment_terms_days)

    # Add colored bar at the top
    pdf.set_fill_color(172, 202, 38)  # #acca26
    pdf.rect(0, 0, 210, 10, 'F')

    # Header title (FACTUUR/INVOICE)
    pdf.set_y(35)  # Moved lower to avoid collision
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(190, 10, invoice_name or trans['invoice'], 0, 1, 'C')

    # Company info in light grey at top right
    pdf.set_text_color(169, 169, 169)
    pdf.set_font('Helvetica', '', 8)
    header_info = {
        "Web": "www.effelekkerschaatsen.com",
        "Address": "Mekelweg 8 2628CD Delft",
        "Mail": "penningmeester@dssvels.com",
        "IBAN": "NL51 ABNA 0552 4048 45",
        "KVK nr": "27183125"
    }

    # Position header info on the right side
    right_column_x = 120
    pdf.set_xy(right_column_x, 45)  # Adjusted Y position
    for key, value in header_info.items():
        pdf.set_x(right_column_x)
        pdf.cell(30, 6, f"{key}:", 0, 0, 'R')
        pdf.cell(0, 6, value, 0, 1, 'L')

    # Customer and invoice details on the left
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_xy(10, 45)  # Adjusted Y position
    
    # Invoice details block
    pdf.cell(95, 8, f"{trans['invoice_number']}: {st.session_state.invoice_number}", 0, 2)
    pdf.cell(95, 8, f"{trans['date']}: {invoice_date.strftime('%Y-%m-%d')}", 0, 2)
    pdf.cell(95, 8, f"{trans['customer']}: {customer_name}", 0, 2)
    pdf.cell(95, 8, f"{trans['due_date']}: {payment_due_date.strftime('%Y-%m-%d')}", 0, 1)
    
    pdf.ln(10)

    # Table header
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 10, trans['description'], 0, 0, 'L', 1)
    pdf.cell(30, 10, trans['quantity'], 0, 0, 'L', 1)
    pdf.cell(40, 10, trans['price'], 0, 0, 'L', 1)
    pdf.cell(40, 10, trans['amount'], 0, 1, 'L', 1)

    # Table content
    pdf.set_font('Helvetica', '', 12)
    total = 0
    for i, line in enumerate(st.session_state.invoice_lines):
        fill = i % 2 == 1
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(80, 10, str(line['description']), 0, 0, 'L', fill)
        pdf.cell(30, 10, str(line['quantity']), 0, 0, 'L', fill)
        pdf.cell(40, 10, f"EUR {line['price']:.2f}", 0, 0, 'L', fill)
        pdf.cell(40, 10, f"EUR {line['amount']:.2f}", 0, 1, 'L', fill)
        total += line['amount']

    # Total line
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(150, 10, f"{trans['total']}:", 0, 0)
    pdf.cell(40, 10, f"EUR {total:.2f}", 0, 1, 'R')

    # Description block
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(169, 169, 169)
    pdf.multi_cell(190, 6, st.session_state.description, 0, 'L')

    # Payment instructions
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(190, 6, trans['payment_instructions'], 0, 'L')

    # Add logo
    try:
        pdf.image('elslogo.png', x=90, y=250, w=30)
    except Exception:
        pass

    # Save to BytesIO
    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)
    
    return pdf_bytes

def add_invoice_line(description, quantity, price):
    amount = float(quantity) * float(price)
    st.session_state.invoice_lines.append({
        'description': description,
        'quantity': quantity,
        'price': price,
        'amount': amount
    })

def clear_invoice_lines():
    st.session_state.invoice_lines.clear()

def generate_test_data():
    clear_invoice_lines()
    test_items = [
        ("Ice skating lesson (1 hour)", 1, 25.00),
        ("Skate rental", 1, 7.50),
        ("Training subscription (monthly)", 1, 45.00),
        ("Competition entry fee", 1, 15.00)
    ]
    for desc, qty, price in test_items:
        add_invoice_line(desc, qty, price)
    return "Test Customer"

def load_config():
    try:
        with open('invoice_config.json', 'r') as f:
            config = json.load(f)
            st.session_state.invoice_number = config.get('last_invoice_number', 1)
            st.session_state.payment_terms_days = config.get('payment_terms_days', 14)
            st.session_state.language = config.get('language', 'nl')
            st.session_state.description = config.get('description', st.session_state.description)
    except FileNotFoundError:
        save_config()

def save_config():
    with open('invoice_config.json', 'w') as f:
        json.dump({
            'last_invoice_number': st.session_state.invoice_number,
            'payment_terms_days': st.session_state.payment_terms_days,
            'language': st.session_state.language,
            'description': st.session_state.description
        }, f)

# Load config at startup
load_config()

# Streamlit UI
st.title("Invoice Generator")

# Settings in sidebar
with st.sidebar:
    st.header("Settings")
    language = st.selectbox(
        "Language",
        options=["Dutch", "English"],
        index=0 if st.session_state.language == 'nl' else 1
    )
    st.session_state.language = 'nl' if language == "Dutch" else 'en'
    
    st.session_state.payment_terms_days = st.number_input(
        "Payment Terms (days)",
        min_value=1,
        value=st.session_state.payment_terms_days
    )

# Main content
st.subheader("Recipient Information")
customer_name = st.text_input("Recipient Name")
invoice_name = st.text_input("Invoice Name (optional)")
description = st.text_area("Invoice Description", value=st.session_state.description, height=100)
st.session_state.description = description

# Invoice Line Items
st.subheader("Add Invoice Line")
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
with col1:
    description = st.text_input("Description", key="description_input")
with col2:
    quantity = st.number_input("Quantity", min_value=0.0, value=1.0, key="quantity_input")
with col3:
    price = st.number_input("Price", min_value=0.0, value=0.0, key="price_input")
with col4:
    if st.button("Add Line"):
        if description and quantity and price:
            add_invoice_line(description, quantity, price)

# Display invoice lines
if st.session_state.invoice_lines:
    st.subheader("Invoice Lines")
    df = pd.DataFrame(st.session_state.invoice_lines)
    edited_df = st.data_editor(
        df,
        column_config={
            "price": st.column_config.NumberColumn("Price", format="€%.2f"),
            "amount": st.column_config.NumberColumn("Amount", format="€%.2f")
        },
        hide_index=True,
        disabled=True
    )

def handle_invoice_generation():
    if not st.session_state.invoice_lines:
        st.error("Please add at least one invoice line.")
        return False
        
    safe_customer_name = re.sub(r'[^\w\-_.]', '_', customer_name)
    pdf_bytes = generate_pdf(customer_name, invoice_name)
    
    # Save to file
    os.makedirs("invoices", exist_ok=True)
    pdf_filename = f"{st.session_state.invoice_number}_{safe_customer_name}.pdf"
    pdf_path = os.path.join("invoices", pdf_filename)
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes.getvalue())
    
    # Store in session state
    st.session_state.current_pdf = pdf_bytes
    st.session_state.current_filename = pdf_filename
    st.session_state.show_download = True
    
    # Save CSV
    csv_filename = f"{st.session_state.invoice_number}_{safe_customer_name}.csv"
    csv_path = os.path.join("invoices", csv_filename)
    df = pd.DataFrame(st.session_state.invoice_lines)
    df['invoice_number'] = st.session_state.invoice_number
    df['customer_name'] = customer_name
    df['date'] = datetime.now().strftime("%Y-%m-%d")
    df.to_csv(csv_path, index=False)
    
    # Update invoice number and save config
    st.session_state.invoice_number += 1
    save_config()
    return True

# Action buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Generate Invoice"):
        if not customer_name:
            st.error("Please fill in recipient name.")
        else:
            handle_invoice_generation()

# Show download section if PDF is generated
if st.session_state.show_download and st.session_state.current_pdf is not None:
    st.success(f"Invoice saved as {st.session_state.current_filename}")
    b64_pdf = base64.b64encode(st.session_state.current_pdf.getvalue()).decode()
    st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="{st.session_state.current_filename}">Download PDF</a>', unsafe_allow_html=True)
    st.markdown("""
    <style>
    .download-button {
        display: inline-block;
        padding: 0.5em 1em;
        color: white;
        background-color: #0066cc;
        text-decoration: none;
        border-radius: 4px;
        margin: 1em 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("Continue to next invoice"):
        st.session_state.show_download = False
        st.session_state.current_pdf = None
        st.session_state.current_filename = None
        clear_invoice_lines()
        st.rerun()

with col2:
    if st.button("Generate Test PDF"):
        customer_name = generate_test_data()
        pdf_bytes = generate_pdf(customer_name, "")
        b64_pdf = base64.b64encode(pdf_bytes.getvalue()).decode()
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="test_invoice.pdf">Download Test PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

with col3:
    if st.button("Clear All"):
        clear_invoice_lines()
        st.rerun()

with col4:
    if st.button("Generate Test Data"):
        customer_name = generate_test_data()
        st.rerun()

# Clipboard functionality
st.subheader("Import from Clipboard")
if st.button("Paste from Clipboard"):
    try:
        df = pd.read_clipboard()
        for _, row in df.iterrows():
            desc = row.get('Description') or row.get('Omschrijving') or str(row.iloc[0])
            qty = row.get('Quantity') or row.get('Aantal') or row.get('Qty') or row.iloc[1]
            price = row.get('Price') or row.get('Prijs') or row.iloc[2]
            add_invoice_line(desc, float(qty), float(price))
        st.rerun()
    except Exception as e:
        st.error(f"Failed to read clipboard: {e}")