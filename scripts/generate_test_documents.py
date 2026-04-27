"""
Script to generate sample Ethiopian National ID documents for testing CLMS verification.
Run: python generate_test_id.py
"""

import os
import sys
import io
import fitz  # PyMuPDF

def create_national_id_pdf(output_path: str, output_filename: str = "sample_national_id.pdf") -> str:
    """
    Creates a realistic Ethiopian National ID PDF document.
    Based on the contractor_spec rules in verification.py
    """

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    # Colors
    dark_blue = (0.05, 0.15, 0.4)
    light_blue = (0.7, 0.85, 0.95)
    black = (0, 0, 0)
    dark_red = (0.5, 0.0, 0.0)

    # --- HEADER ---
    # Ethiopian government header background
    page.draw_rect(fitz.Rect(0, 0, 595, 120), color=dark_blue, fill=dark_blue)

    # Title - Federal Democratic Republic of Ethiopia
    page.insert_text(
        (100, 45),
        "FEDERAL DEMOCRATIC REPUBLIC OF ETHIOPIA",
        fontsize=14,
        color=(1, 1, 1),
        fontname="helv"
    )

    page.insert_text(
        (180, 70),
        "National Identity Card",
        fontsize=14,
        color=(1, 1, 1),
        fontname="helv"
    )

    # Subtitle in Amharic (using ASCII replacement)
    page.insert_text(
        (170, 95),
        "( YorDEmhrAs Yd~hL~n )",
        fontsize=11,
        color=(1, 1, 1),
        fontname="helv"
    )

    # --- ID CONTENT AREA ---
    y = 140

    # ID Label and Number
    page.insert_text((50, y), "ID Number:", fontsize=11, color=black, fontname="helv")
    page.insert_text((160, y), "0000123456789", fontsize=12, color=black, fontname="helv")
    page.draw_rect(fitz.Rect(155, y - 12, 330, y + 3), color=black, fill=None)

    y += 30

    # Photo placeholder box
    page.draw_rect(fitz.Rect(50, y, 180, y + 150), color=black, fill=light_blue)
    page.insert_text((70, y + 80), "PHOTO", fontsize=14, color=dark_blue, fontname="helv")

    # --- FIELDS ON THE RIGHT OF PHOTO ---
    x_field = 200
    y_field = y + 20

    fields = [
        ("Full Name (English):", "JOHN DOE SMITH"),
        ("Full Name (Amharic):", "ጆን ዶ ስሚዝ"),
        ("Father's Name:", "MICHAEL SMITH"),
        ("Grandfather's Name:", "JAMES SMITH"),
        ("Date of Birth:", "15/08/1990"),
        ("Sex:", "M"),
        ("Nationality:", "Ethiopian"),
    ]

    for label, value in fields:
        page.insert_text((x_field, y_field), label, fontsize=10, color=black, fontname="helv")
        page.insert_text((x_field, y_field + 15), value, fontsize=11, color=black, fontname="helv")
        y_field += 30

    y = y + 170

    # --- MORE FIELDS ---
    y += 10

    page.insert_text((50, y), "FAN (Federal ID Number):", fontsize=10, color=black, fontname="helv")
    page.insert_text((230, y), "0000123456789", fontsize=11, color=black, fontname="helv")
    y += 25

    page.insert_text((50, y), "Address:", fontsize=10, color=black, fontname="helv")
    page.insert_text((130, y), "Addis Ababa, Ethiopia", fontsize=11, color=black, fontname="helv")
    y += 25

    page.insert_text((50, y), "Region:", fontsize=10, color=black, fontname="helv")
    page.insert_text((130, y), "Addis Ababa", fontsize=11, color=black, fontname="helv")
    y += 25

    page.insert_text((50, y), "Zone:", fontsize=10, color=black, fontname="helv")
    page.insert_text((130, y), "Central", fontsize=11, color=black, fontname="helv")
    y += 25

    page.insert_text((50, y), "Wereda:", fontsize=10, color=black, fontname="helv")
    page.insert_text((130, y), "04", fontsize=11, color=black, fontname="helv")
    y += 25

    # --- DATES ---
    page.insert_text((50, y), "Issue Date:", fontsize=10, color=black, fontname="helv")
    page.insert_text((140, y), "01/01/2020", fontsize=11, color=black, fontname="helv")
    page.insert_text((280, y), "Expiry Date:", fontsize=10, color=black, fontname="helv")
    page.insert_text((370, y), "01/01/2030", fontsize=11, color=black, fontname="helv")
    y += 40

    # --- STAMP PLACEHOLDER ---
    page.draw_rect(fitz.Rect(400, y - 30, 550, y + 40), color=dark_red, fill=None)
    page.insert_text((410, y), "OFFICIAL", fontsize=10, color=dark_red, fontname="helv")
    page.insert_text((410, y + 15), "STAMP", fontsize=10, color=dark_red, fontname="helv")

    # --- QR CODE PLACEHOLDER ---
    page.draw_rect(fitz.Rect(50, y - 30, 120, y + 40), color=black, fill=None)
    page.insert_text((55, y), "QR CODE", fontsize=9, color=black, fontname="helv")

    # --- SERIAL NUMBER ---
    page.insert_text((50, y + 60), "Serial Number:", fontsize=9, color=black, fontname="helv")
    page.insert_text((130, y + 60), "SN-2020-00001", fontsize=9, color=black, fontname="helv")

    # Save the PDF
    full_path = os.path.join(output_path, output_filename)
    doc.save(full_path)
    doc.close()

    print(f"National ID PDF created: {full_path}")
    return full_path


def create_tax_certificate_pdf(output_path: str, output_filename: str = "sample_tax_certificate.pdf") -> str:
    """
    Creates a realistic Ethiopian Tax Registration Certificate PDF.
    """

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    dark_blue = (0.05, 0.15, 0.4)
    light_blue = (0.7, 0.85, 0.95)
    black = (0, 0, 0)
    dark_red = (0.5, 0.0, 0.0)

    # --- HEADER ---
    page.draw_rect(fitz.Rect(0, 0, 595, 100), color=dark_blue, fill=dark_blue)

    page.insert_text(
        (100, 40),
        "MINISTRY OF REVENUE",
        fontsize=18,
        color=(1, 1, 1),
        fontname="helv"
    )
    page.insert_text(
        (120, 65),
        "MINISTRY OF REVENUE",
        fontsize=12,
        color=(1, 1, 1),
        fontname="helv"
    )
    page.insert_text(
        (180, 85),
        "Taxpayer Registration Certificate",
        fontsize=11,
        color=(1, 1, 1),
        fontname="helv"
    )

    y = 130

    # TIN Box
    page.draw_rect(fitz.Rect(50, y, 495, y + 60), color=dark_blue, fill=light_blue)
    page.insert_text((60, y + 20), "TAX IDENTIFICATION NUMBER (TIN)", fontsize=10, color=dark_blue, fontname="helv")
    page.insert_text((60, y + 45), "1234567890", fontsize=24, color=dark_blue, fontname="helv")

    y += 85

    # Taxpayer Name
    page.insert_text((50, y), "Taxpayer Name (English):", fontsize=11, color=black, fontname="helv")
    y += 20
    page.insert_text((50, y), "ABC CONSTRUCTION PLC", fontsize=14, color=black, fontname="helv")
    y += 30

    page.insert_text((50, y), "Taxpayer Name (Amharic):", fontsize=11, color=black, fontname="helv")
    y += 20
    page.insert_text((50, y), "ABC CONSTRUCTION PLC (Amharic)", fontsize=14, color=black, fontname="helv")
    y += 40

    # Details grid
    details = [
        ("TIN:", "1234567890"),
        ("Registration Date:", "15/03/2018"),
        ("Tax Office:", "Addis Ababa Large Taxpayers Office"),
        ("Tax Type:", "Business Income Tax"),
        ("Business Activity:", "General Construction"),
        ("Status:", "Active"),
    ]

    for label, value in details:
        page.insert_text((50, y), label, fontsize=11, color=black, fontname="helv")
        page.insert_text((200, y), value, fontsize=11, color=black, fontname="helv")
        y += 25

    y += 30

    # Stamps
    page.draw_rect(fitz.Rect(400, y, 540, y + 60), color=dark_red, fill=None)
    page.insert_text((410, y + 30), "OFFICIAL STAMP", fontsize=10, color=dark_red, fontname="helv")

    page.draw_rect(fitz.Rect(50, y, 150, y + 60), color=black, fill=None)
    page.insert_text((55, y + 30), "QR CODE", fontsize=9, color=black, fontname="helv")

    # Save
    full_path = os.path.join(output_path, output_filename)
    doc.save(full_path)
    doc.close()

    print(f"Tax Certificate PDF created: {full_path}")
    return full_path


def create_experience_certificate_pdf(output_path: str, output_filename: str = "sample_experience_certificate.pdf") -> str:
    """
    Creates a realistic Experience Certificate PDF.
    """

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    black = (0, 0, 0)
    dark_blue = (0.05, 0.15, 0.4)

    y = 80

    # Company Header
    page.insert_text((180, y), "ABC CONSTRUCTION PLC", fontsize=18, color=dark_blue, fontname="helv")
    y += 25
    page.insert_text((150, y), "Kifle Ketema, Addis Ababa, Ethiopia", fontsize=10, color=black, fontname="helv")
    y += 20
    page.insert_text((230, y), "Tel: +251-11-123-4567", fontsize=10, color=black, fontname="helv")
    y += 30

    page.draw_line((50, y), (545, y), color=dark_blue, width=2)
    y += 30

    page.insert_text((220, y), "EXPERIENCE CERTIFICATE", fontsize=16, color=dark_blue, fontname="helv")
    y += 50

    # Certificate body
    page.insert_text((50, y), "This is to certify that:", fontsize=11, color=black, fontname="helv")
    y += 30

    page.insert_text((50, y), "Mr. Abraham Bekele Worku", fontsize=13, color=black, fontname="helv")
    y += 25

    page.insert_text((50, y), "has successfully completed the following construction project:", fontsize=11, color=black, fontname="helv")
    y += 35

    # Project details box
    page.draw_rect(fitz.Rect(50, y, 545, y + 180), color=black, fill=None)

    project_fields = [
        ("Project Name:", "Addis Ababa Central Hospital Expansion"),
        ("Project Location:", "Addis Ababa, Ethiopia"),
        ("Project Value:", "ETB 50,000,000.00"),
        ("Position Held:", "Site Engineer"),
        ("Start Date:", "01/06/2020"),
        ("End Date:", "30/11/2022"),
        ("Duration:", "30 months"),
    ]

    yp = y + 20
    for label, value in project_fields:
        page.insert_text((60, yp), label, fontsize=10, color=black, fontname="helv")
        page.insert_text((200, yp), value, fontsize=10, color=black, fontname="helv")
        yp += 25

    y += 200

    page.insert_text((50, y), "The project was executed according to the highest professional standards.", fontsize=11, color=black, fontname="helv")
    y += 30
    page.insert_text((50, y), "We recommend him for any challenging construction projects.", fontsize=11, color=black, fontname="helv")

    y += 60

    # Signature area
    page.insert_text((50, y), "Authorized Signature:", fontsize=10, color=black, fontname="helv")
    page.draw_line((50, y + 30), (200, y + 30), color=black, width=1)

    page.draw_rect(fitz.Rect(400, y - 30, 540, y + 60), color=black, fill=None)
    page.insert_text((410, y + 10), "COMPANY STAMP", fontsize=10, color=black, fontname="helv")

    full_path = os.path.join(output_path, output_filename)
    doc.save(full_path)
    doc.close()

    print(f"Experience Certificate PDF created: {full_path}")
    return full_path


def main():
    # Output directory - same folder as script
    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    print("Generating CLMS Test Documents")
    print("=" * 50)

    try:
        # Generate all sample documents
        create_national_id_pdf(output_dir, "sample_national_id.pdf")
        create_tax_certificate_pdf(output_dir, "sample_tax_certificate.pdf")
        create_experience_certificate_pdf(output_dir, "sample_experience_certificate.pdf")

        print("\n" + "=" * 50)
        print("All documents generated successfully!")
        print(f"Output directory: {output_dir}")
        print("=" * 50)

    except Exception as e:
        print(f"Error generating documents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
