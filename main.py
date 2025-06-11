import dearpygui.dearpygui as dpg
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import json
import re # Added for filename sanitization

class InvoiceManager:    
    def __init__(self):
        self.invoice_lines = []
        self.invoice_number = 1
        self.payment_terms_days = 14
        self.language = 'nl'  # Default to Dutch
        self.description = "Invoice for ice skating activities at DSSV ELS."
        self.translations = {
            'nl': {
                'invoice': 'FACTUUR',
                'invoice_number': 'Factuurnummer',
                'date': 'Datum',
                'customer': 'Ontvanger',
                'due_date': 'Vervaldatum',
                'description': 'Omschrijving',
                'quantity': 'Aantal',
                'price': 'Stukprijs',
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
        self.load_config()
        
    def load_config(self):
        try:
            with open('invoice_config.json', 'r') as f:
                config = json.load(f)
                self.invoice_number = config.get('last_invoice_number', 1)
                self.payment_terms_days = config.get('payment_terms_days', 14)
                self.language = config.get('language', 'nl')
                self.description = config.get('description', self.description)
        except FileNotFoundError:
            self.save_config()
    
    def save_config(self):
        with open('invoice_config.json', 'w') as f:
            json.dump({
                'last_invoice_number': self.invoice_number,
                'payment_terms_days': self.payment_terms_days,
                'language': self.language,
                'description': self.description
            }, f)

    def add_line(self, description, quantity, price):
        amount = float(quantity) * float(price)
        self.invoice_lines.append({
            'description': description,
            'quantity': quantity,
            'price': price,
            'amount': amount
        })
        return len(self.invoice_lines) - 1

    def remove_line(self, index):
        if 0 <= index < len(self.invoice_lines):
            self.invoice_lines.pop(index)

    def clear_lines(self):
        self.invoice_lines.clear()    
    
    def generate_pdf(self, customer_name, invoice_name, save_path, invoice_number_to_display):
        pdf = FPDF()
        # Add Tahoma font
        pdf.add_font('Tahoma', '', r'C:\Windows\Fonts\tahoma.ttf', uni=True)
        pdf.add_font('Tahoma', 'B', r'C:\Windows\Fonts\tahomabd.ttf', uni=True)
        pdf.add_page('P', 'A4')
    
        # Initialize translations and dates
        trans = self.translations[self.language]
        invoice_date = datetime.now()
        payment_due_date = invoice_date + pd.Timedelta(days=self.payment_terms_days)

        # Add colored bar at the top
        pdf.set_fill_color(172, 202, 38)  # #acca26
        pdf.rect(0, 0, 210, 10, 'F')

        # Header title (FACTUUR/INVOICE)
        pdf.set_y(35)  # Moved down to avoid collision
        pdf.set_font('Tahoma', 'B', 16)
        pdf.cell(190, 10, invoice_name or trans['invoice'], 0, 1, 'C')

        # Company info in light grey at top right
        pdf.set_text_color(169, 169, 169)
        pdf.set_font('Tahoma', '', 8)
        header_info = {
            "Name": "DSSV ELS",
            "Web": "www.effelekkerschaatsen.com",
            "Address": "Mekelweg 8 2628CD Delft",
            "Mail": "penningmeester@dssvels.com",
            "IBAN": "NL51 ABNA 0552 4048 45",
            "KVK nr": "27183125"
        }

        # Position header info on the right side
        right_column_x = 120
        pdf.set_xy(right_column_x, 45)
        for key, value in header_info.items():
            x_pos = pdf.get_x()
            pdf.set_x(right_column_x)
            pdf.cell(30, 6, f"{key}:", 0, 0, 'R')
            pdf.cell(0, 6, value, 0, 1, 'L')

        # Customer and invoice details on the left
        pdf.set_text_color(169, 169, 169)
        pdf.set_font('Tahoma', '', 8)
        pdf.set_xy(10, 45)
        
        
        # Invoice details block
        pdf.cell(95, 8, f"{trans['invoice_number']}: {invoice_number_to_display}", 0, 2)
        pdf.cell(95, 8, f"{trans['date']}: {invoice_date.strftime('%Y-%m-%d')}", 0, 2)
        pdf.cell(95, 8, f"{trans['customer']}: {customer_name}", 0, 2)
        pdf.cell(95, 8, f"{trans['due_date']}: {payment_due_date.strftime('%Y-%m-%d')}", 0, 1)
        
        # Move to position for table
        pdf.ln(10)
        pdf.set_text_color(0,0,0)
        # Table header
        pdf.set_font('Tahoma', 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(80, 10, trans['description'], 0, 0, 'L', 1)
        pdf.cell(30, 10, trans['quantity'], 0, 0, 'L', 1)
        pdf.cell(40, 10, trans['price'], 0, 0, 'L', 1)
        pdf.cell(40, 10, trans['amount'], 0, 1, 'L', 1)

        # Table content
        pdf.set_font('Tahoma', '', 10)
        total = 0
        for i, line in enumerate(self.invoice_lines):
            # Alternate row colors
            fill = i % 2 == 1
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(80, 10, str(line['description']), 0, 0, 'L', fill)
            pdf.cell(30, 10, str(line['quantity']), 0, 0, 'L', fill)
            pdf.cell(40, 10, f"€ {line['price']:.2f}", 0, 0, 'L', fill)
            pdf.cell(40, 10, f"€ {line['amount']:.2f}", 0, 1, 'L', fill)
            total += line['amount']

        # Total line
        pdf.ln(2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('Tahoma', 'B', 11)        
        pdf.cell(150, 10, f"{trans['total']}:", 0, 0)
        pdf.cell(40, 10, f"€ {total:.2f}", 0, 1, 'R')

        # Description block
        pdf.ln(5)
        pdf.set_font('Tahoma', '', 10)
        pdf.set_text_color(169, 169, 169)
        pdf.multi_cell(190, 6, self.description, 0, 'L')
        
        # Payment instructions
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Tahoma', '', 10)
        pdf.multi_cell(190, 6, trans['payment_instructions'], 0, 'L')

        # Add logo at the bottom of the page (footer) without distortion and at a visible position
        try:
            pdf.image('elslogo.png', x=90, y=250, w=30)
        except Exception:
            pass

        # Save PDF
        pdf.output(save_path)
        # Note: Invoice number increment and config save moved to GUI layer

    def save_to_csv(self, customer_name, save_path, invoice_number_to_use):
        df = pd.DataFrame(self.invoice_lines)
        df['invoice_number'] = invoice_number_to_use
        df['customer_name'] = customer_name
        df['date'] = datetime.now().strftime("%Y-%m-%d")
        df.to_csv(save_path, index=False)

    def add_lines_from_clipboard(self):
        import pandas as pd
        try:
            df = pd.read_clipboard()
            for _, row in df.iterrows():
                # Try to find columns for description, quantity, price
                desc = row.get('Description') or row.get('Omschrijving') or str(row.iloc[0])
                qty = row.get('Quantity') or row.get('Aantal') or row.get('Qty') or row.get('Aantal') or row.iloc[1]
                price = row.get('Price') or row.get('Prijs') or row.iloc[2]
                self.add_line(desc, qty, price)
        except Exception as e:
            print(f"Failed to read clipboard: {e}")

    def generate_test_data(self):
        """Generate dummy data for testing"""
        self.clear_lines()
        test_items = [
            ("Ice skating lesson (1 hour)", 1, 25.00),
            ("Skate rental", 1, 7.50),
            ("Training subscription (monthly)", 1, 45.00),
            ("Competition entry fee", 1, 15.00)
        ]
        for desc, qty, price in test_items:
            self.add_line(desc, qty, price)
        return "Test Customer"

class InvoiceGUI:
    def __init__(self):
        self.invoice_manager = InvoiceManager()
        self.setup_gui()
        
    def setup_gui(self):
        dpg.create_context()
        dpg.create_viewport(title="Invoice Generator", width=800, height=600)
        
        # Create error popup window
        with dpg.window(label="Error", modal=True, show=False, tag="error_popup", width=300, height=100, pos=[250, 250]):
            dpg.add_text("Please fill in all required fields!")
            dpg.add_button(label="OK", callback=lambda: dpg.hide_item("error_popup"), width=75)
        
        with dpg.window(label="Invoice Generator", tag="primary_window"):            # Customer Information
            dpg.add_text("Recipient Information")
            dpg.add_input_text(label="Recipient Name", tag="customer_name")
            dpg.add_input_text(label="Invoice Name (optional)", tag="invoice_name", default_value="")
            dpg.add_input_text(label="Invoice Description", tag="invoice_description", default_value=self.invoice_manager.description, width=400)
            
            # Invoice Line Items
            dpg.add_text("Add Invoice Line")
            dpg.add_input_text(label="Description", tag="description")
            dpg.add_input_float(label="Quantity", tag="quantity", default_value=1)
            dpg.add_input_float(label="Price", tag="price", default_value=0.00)
            dpg.add_button(label="Add Line", callback=self.add_line_callback)
            
            # Invoice Lines Table
            with dpg.table(header_row=True, tag="invoice_table"):
                dpg.add_table_column(label="Description")
                dpg.add_table_column(label="Quantity")
                dpg.add_table_column(label="Price")
                dpg.add_table_column(label="Amount")
                dpg.add_table_column(label="Actions")
            
            # Settings
            dpg.add_text("Settings")
            dpg.add_input_int(label="Payment Terms (days)", tag="payment_terms", default_value=14, callback=self.update_payment_terms)
            dpg.add_combo(label="Language", items=["Dutch", "English"], default_value="Dutch" if self.invoice_manager.language == 'nl' else "English", 
                         callback=self.update_language, tag="language_selector")
              # Invoice Line Management
            with dpg.group(horizontal=True):
                dpg.add_button(label="Paste from Clipboard", callback=self.paste_lines_callback)
                dpg.add_button(label="Clear All Lines", callback=self.clear_all_callback)
            
            # Generate Options
            dpg.add_text("Generate Options")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Generate Invoice", callback=self.generate_invoice_callback)
                dpg.add_button(label="Generate Test PDF", callback=self.generate_test_pdf_callback)
            dpg.add_button(label="Generate Test Data", callback=self.generate_test_data_callback)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary_window", True)
        dpg.start_dearpygui()
        
    def sanitize_filename(self, filename_str):
        """
        Sanitizes a string to be used as a filename.
        Replaces spaces with underscores.
        Removes characters that are not alphanumeric, underscore, hyphen, or period.
        If the result is empty or invalid, returns a default name.
        """
        if not filename_str:
            return "untitled"
        
        s = str(filename_str).replace(" ", "_")
        s = re.sub(r'[^\w\._-]', '', s)
        s = s.strip('_-.') # Remove leading/trailing problematic chars

        if not s or all(c in '_-.' for c in s):
            # If empty after sanitization or only consists of separators
            # (e.g. customer name was "...")
            return "sanitized_recipient" 
            
        return s

    def clear_invoice_lines_and_inputs(self):
        """Clears only the invoice lines and their input fields."""
        self.invoice_manager.clear_lines()
        # Clear line item input fields
        dpg.set_value("description", "")  # Line item description input
        dpg.set_value("quantity", 1)
        dpg.set_value("price", 0.00)
        self.update_table()
        
    def update_language(self, sender, app_data):
        self.invoice_manager.language = 'nl' if app_data == "Dutch" else 'en'
        self.invoice_manager.save_config()
        
    def update_payment_terms(self, sender, app_data):
        self.invoice_manager.payment_terms_days = app_data
        self.invoice_manager.save_config()
        
    def add_line_callback(self):
        description = dpg.get_value("description")
        quantity = dpg.get_value("quantity")
        price = dpg.get_value("price")
        
        if description and quantity and price:
            index = self.invoice_manager.add_line(description, quantity, price)
            self.update_table()
            
            # Clear inputs
            dpg.set_value("description", "")
            dpg.set_value("quantity", 1)
            dpg.set_value("price", 0.00)
            
    def update_table(self):
        # Clear existing rows
        if dpg.does_item_exist("invoice_table"):
            children = dpg.get_item_children("invoice_table")[1]
            for child in children:
                dpg.delete_item(child)
        
        # Add new rows
        for i, line in enumerate(self.invoice_manager.invoice_lines):
            with dpg.table_row(parent="invoice_table"):
                dpg.add_text(line['description'])
                dpg.add_text(f"{line['quantity']}")
                dpg.add_text(f"{line['price']:.2f}")
                dpg.add_text(f"{line['amount']:.2f}")
                dpg.add_button(label="Delete", callback=lambda s, a, u: self.delete_line_callback(u), user_data=i)
                
    def delete_line_callback(self, index):
        self.invoice_manager.remove_line(index)
        self.update_table()
        
    def generate_invoice_callback(self):
        customer_name = dpg.get_value("customer_name")
        invoice_name = dpg.get_value("invoice_name")
        if not customer_name:
            dpg.show_item("error_popup")
            return

        gui_invoice_description = dpg.get_value("invoice_description")
        if not gui_invoice_description: # Assuming invoice description is also required
            dpg.show_item("error_popup")
            return
        
        if not self.invoice_manager.invoice_lines:
            dpg.show_item("error_popup")
            return
        
        current_invoice_number = self.invoice_manager.invoice_number
        safe_customer_name = self.sanitize_filename(customer_name)

        # Create output directory if it doesn't exist
        os.makedirs("invoices", exist_ok=True)
        
        # Update the invoice manager's description with the value from the GUI
        self.invoice_manager.description = gui_invoice_description

        pdf_filename = f"{current_invoice_number}_{safe_customer_name}.pdf"
        csv_filename = f"{current_invoice_number}_{safe_customer_name}.csv"
        pdf_path = os.path.join("invoices", pdf_filename)
        csv_path = os.path.join("invoices", csv_filename)

        # Generate PDF
        self.invoice_manager.generate_pdf(customer_name, invoice_name, pdf_path, current_invoice_number)
        
        # Save CSV
        self.invoice_manager.save_to_csv(customer_name, csv_path, current_invoice_number)
        
        # Increment invoice number and save config AFTER successful generation
        self.invoice_manager.invoice_number += 1
        self.invoice_manager.save_config()
        # Clear form for next invoice
        self.clear_invoice_lines_and_inputs() # Keep customer, invoice name, and invoice description
        
    def clear_all_callback(self):
        self.invoice_manager.clear_lines()
        dpg.set_value("customer_name", "")
        dpg.set_value("invoice_name", "")
        dpg.set_value("description", "")
        dpg.set_value("quantity", 1)
        dpg.set_value("price", 0.00)
        # Note: invoice_description field (overall invoice description) is not cleared here by default
        self.update_table()
        
    def paste_lines_callback(self):
        self.invoice_manager.add_lines_from_clipboard()
        self.update_table()
        
    def generate_test_data_callback(self):
        customer_name = self.invoice_manager.generate_test_data()
        dpg.set_value("customer_name", customer_name)
        self.update_table()
        
    def generate_test_pdf_callback(self):
        """Generate a test PDF with dummy data"""
        customer_name = self.invoice_manager.generate_test_data()
        dpg.set_value("customer_name", customer_name) # Reflect test customer in GUI
        dpg.set_value("invoice_name", "Test Invoice") # Optional: set test invoice name
        self.update_table() # Update table with test lines

        current_invoice_number = self.invoice_manager.invoice_number
        safe_customer_name = self.sanitize_filename(customer_name) # Will be "Test_Customer"
        invoice_name_for_pdf = dpg.get_value("invoice_name") or "Test Invoice"
        
        # Create output directory if it doesn't exist
        os.makedirs("invoices", exist_ok=True)
        
        pdf_filename = f"{current_invoice_number}_{safe_customer_name}_TEST.pdf" # Added _TEST to distinguish
        csv_filename = f"{current_invoice_number}_{safe_customer_name}_TEST.csv" # Added _TEST
        pdf_path = os.path.join("invoices", pdf_filename)
        csv_path = os.path.join("invoices", csv_filename)

        # Generate PDF with test data
        self.invoice_manager.generate_pdf(customer_name, invoice_name_for_pdf, pdf_path, current_invoice_number)
        
        # Save CSV
        self.invoice_manager.save_to_csv(customer_name, csv_path, current_invoice_number)
        
        # Increment invoice number and save config AFTER successful generation
        self.invoice_manager.invoice_number += 1
        self.invoice_manager.save_config()

        # Clear form for next invoice
        self.clear_all_callback() # Clears all fields including customer name for test

if __name__ == "__main__":
    gui = InvoiceGUI()