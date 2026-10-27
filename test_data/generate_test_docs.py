"""
TrustLens Synthetic Test Data Generation Script
Generates 7 synthetic test documents in test_data/samples/ for SIH MVP testing.

Dependencies:
    - fpdf2 (fpdf2==2.7.9)
    - Pillow (Pillow==10.3.0)
"""

import os
import sys
import hashlib
from pathlib import Path

# Dependency imports with clear error messages
try:
    from fpdf import FPDF
except ImportError as exc:
    print("[ERROR] fpdf2 is not installed.")
    print("Please install it using: pip install fpdf2==2.7.9")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    print("[ERROR] Pillow is not installed.")
    print("Please install it using: pip install Pillow==10.3.0")
    sys.exit(1)


class TrustLensPDF(FPDF):
    """Custom FPDF class with AICTE synthetic test watermark and header/footer."""

    def __init__(self, watermark_text="SYNTHETIC TEST DOCUMENT - NOT REAL", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watermark_text = watermark_text

    def header(self):
        # Header banner
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION (AICTE) - SCRUTINY MVP DEMO", border="B", ln=True, align="C")
        self.ln(4)

    def footer(self):
        # Footer notice
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, self.watermark_text, ln=True, align="C")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}} | TrustLens Synthetic Test Data", align="C")

    def draw_watermark(self):
        """Draws diagonal translucent-looking watermark across the page."""
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(220, 220, 220)
        # Safe rotation context manager in fpdf2
        try:
            with self.rotation(36, x=105, y=148):
                self.text(15, 148, self.watermark_text)
        except Exception:
            # Fallback for plain header watermark if rotation unsupported
            self.set_xy(10, 25)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(210, 210, 210)
            self.cell(0, 10, f"*** {self.watermark_text} ***", align="C")


def generate_sample_01(output_dir: Path) -> Path:
    """Sample 01: Complete consistent application document with all mandatory fields."""
    file_path = output_dir / "sample_01_complete.pdf"
    pdf = TrustLensPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.draw_watermark()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(20, 50, 120)
    pdf.cell(0, 12, "AICTE APPROVAL PROCESS APPLICATION 2024-25", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Part A: Institutional Identity & Governance Details", ln=True, align="L")
    pdf.ln(3)

    fields = [
        ("Institution Name", "Vigyan Engineering College"),
        ("Application No", "AICTE-2024-VEC-001"),
        ("Address", "45 Tech Park Road, Pune, Maharashtra 411001"),
        ("Director", "Dr. Priya Sharma"),
        ("Phone", "+91-9876543210"),
        ("Email", "director@vigyanec.edu.in"),
        ("Established", "2005"),
        ("Affiliated to", "Savitribai Phule Pune University"),
        ("Total Intake", "480"),
        ("Programs", "B.Tech (CSE, ECE, ME, CE)"),
    ]

    pdf.set_font("Helvetica", "", 10)
    for label, value in fields:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(50, 7, f"{label}:", border=1, ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(140, 7, f" {value}", border=1, ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 80, 40)
    pdf.cell(0, 7, "Institutional Undertaking & Declaration", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(70, 70, 70)
    undertaking_text = (
        "I, Dr. Priya Sharma, Director of Vigyan Engineering College, hereby declare that the "
        "information furnished above is true, complete, and correct to the best of my knowledge and belief. "
        "The institution complies with AICTE Approval Process Handbook (APH) regulations regarding land, "
        "built-up area, faculty-student ratio, and laboratory infrastructure for the sanctioned intake of 480 seats."
    )
    pdf.multi_cell(0, 5, undertaking_text)

    pdf.ln(12)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(95, 6, "Authorized Signatory: Dr. Priya Sharma", ln=False)
    pdf.cell(95, 6, "Date: 15-January-2024", ln=True, align="R")

    pdf.output(str(file_path))
    return file_path


def generate_sample_02a(output_dir: Path) -> Path:
    """Sample 02a: Mismatch pair document 1 (Institution: ABC Technical Institute)."""
    file_path = output_dir / "sample_02a_mismatch.pdf"
    pdf = TrustLensPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.draw_watermark()

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(160, 40, 40)
    pdf.cell(0, 10, "AFFILIATION CERTIFICATE / RECORD - DOCUMENT A", ln=True, align="C")
    pdf.ln(3)

    fields = [
        ("Institution Name", "ABC Technical Institute"),
        ("Application No", "AICTE-2024-ABC-002"),
        ("Address", "Plot 12, Industrial Area, Sector 5, Navi Mumbai 400705"),
        ("Director", "Prof. R. K. Verma"),
        ("Phone", "+91-9822011223"),
        ("Email", "principal@abctech.edu.in"),
        ("Established", "2010"),
        ("Affiliated to", "Mumbai University"),
        ("Total Intake", "300"),
    ]

    for label, value in fields:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(50, 7, f"{label}:", border=1, ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(140, 7, f" {value}", border=1, ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Submitted as Primary Institutional Dossier to AICTE Scrutiny Committee.")
    pdf.output(str(file_path))
    return file_path


def generate_sample_02b(output_dir: Path) -> Path:
    """Sample 02b: Mismatch pair document 2 (Institution: XYZ Technology College, Same App No)."""
    file_path = output_dir / "sample_02b_mismatch.pdf"
    pdf = TrustLensPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.draw_watermark()

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(160, 40, 40)
    pdf.cell(0, 10, "LAND & INFRASTRUCTURE TITLE DEED - DOCUMENT B", ln=True, align="C")
    pdf.ln(3)

    fields = [
        ("Institution Name", "XYZ Technology College"),  # Deliberate mismatch with 02a
        ("Application No", "AICTE-2024-ABC-002"),      # Same Application ID to trigger cross-doc comparison
        ("Address", "Survey 44, Tech Corridor, Hinjawadi, Pune 411057"),
        ("Director", "Prof. R. K. Verma"),
        ("Phone", "+91-9822011223"),
        ("Email", "registrar@xyztech.org"),
        ("Established", "2010"),
        ("Affiliated to", "Mumbai University"),
        ("Total Intake", "300"),
    ]

    for label, value in fields:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(50, 7, f"{label}:", border=1, ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(140, 7, f" {value}", border=1, ln=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Submitted as Supporting Land Title Document. Notice: Institution Name differs from Document A.")
    pdf.output(str(file_path))
    return file_path


def generate_sample_03(output_dir: Path) -> Path:
    """Sample 03: Missing several mandatory fields (no institution name, email, address, director)."""
    file_path = output_dir / "sample_03_missing_fields.pdf"
    pdf = TrustLensPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.draw_watermark()

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(180, 100, 20)
    pdf.cell(0, 10, "PRELIMINARY APPLICATION SUMMARY (INCOMPLETE)", ln=True, align="C")
    pdf.ln(4)

    # Only 2 fields present, missing mandatory institution name, director, email, address
    fields = [
        ("Application No", "AICTE-2024-MF-003"),
        ("Phone", "+91-9876500001"),
    ]

    for label, value in fields:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(50, 7, f"{label}:", border=1, ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(10, 10, 10)
        pdf.cell(140, 7, f" {value}", border=1, ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(150, 40, 40)
    pdf.multi_cell(0, 6, "Notice: Mandatory fields (Institution Name, Registered Address, Director Name, Contact Email) were omitted in this submission.")
    pdf.output(str(file_path))
    return file_path


def generate_sample_04_duplicates(output_dir: Path) -> tuple[Path, Path]:
    """Sample 04a and 04b: Identical PNG images with matching SHA-256 hash."""
    file_path_a = output_dir / "sample_04a_duplicate.png"
    file_path_b = output_dir / "sample_04b_duplicate.png"

    width, height = 800, 600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Outer decorative border
    draw.rectangle([(20, 20), (780, 580)], outline=(30, 60, 120), width=4)
    draw.rectangle([(28, 28), (772, 572)], outline=(180, 180, 180), width=1)

    # Content
    draw.text((220, 70), "CERTIFICATE OF AFFILIATION", fill=(20, 40, 100))
    draw.text((250, 130), "Vigyan Engineering College", fill=(40, 40, 40))
    draw.text((180, 200), "This certifies affiliation under Savitribai Phule Pune University", fill=(60, 60, 60))
    draw.text((260, 240), "for Academic Year 2024-2025", fill=(60, 60, 60))

    # Watermark / Marker text
    draw.text((210, 450), "SYNTHETIC DUPLICATE TEST", fill=(180, 180, 180))
    draw.text((180, 480), "Exact bitwise duplicate for SHA-256 match", fill=(180, 180, 180))

    # Save 04a
    img.save(file_path_a, format="PNG")

    # Read binary bytes of 04a and write identically to 04b to guarantee bitwise SHA-256 identity
    with open(file_path_a, "rb") as f_in:
        content_bytes = f_in.read()

    with open(file_path_b, "wb") as f_out:
        f_out.write(content_bytes)

    return file_path_a, file_path_b


def generate_sample_05_altered(output_dir: Path) -> Path:
    """Sample 05: PNG image simulating document with a visually altered / erased region."""
    file_path = output_dir / "sample_05_altered.png"

    width, height = 800, 600
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    # Document border
    draw.rectangle([(20, 20), (780, 580)], outline=(80, 80, 80), width=3)

    # Header
    draw.text((220, 50), "LAND & OCCUPANCY CERTIFICATE", fill=(20, 30, 80))
    draw.text((100, 120), "Institution: Vigyan Engineering College", fill=(40, 40, 40))
    draw.text((100, 160), "Sanctioned Built-Up Area: 14,250 sq. meters", fill=(40, 40, 40))
    draw.text((100, 200), "Approved Floor Space Index (FSI): 1.75", fill=(40, 40, 40))
    draw.text((100, 240), "Total Campus Land Area: 5.50 Acres (Contiguous)", fill=(40, 40, 40))

    # Simulated official stamp circle
    draw.ellipse([(550, 150), (700, 300)], outline=(180, 40, 40), width=3)
    draw.text((580, 210), "GOVT SEAL", fill=(180, 40, 40))
    draw.text((575, 230), "VERIFIED", fill=(180, 40, 40))

    # Visually altered / erased patch over land area text
    # Draw pure white rectangle over land area and seal section to simulate digital whiteout/tampering
    draw.rectangle([(260, 235), (520, 265)], fill=(255, 255, 255), outline=(230, 230, 230), width=1)
    draw.text((270, 242), "[MODIFIED: 9.80 ACRES]", fill=(120, 120, 120))

    # Label
    draw.text((230, 480), "SYNTHETIC ALTERATION TEST", fill=(200, 30, 30))
    draw.text((180, 510), "Simulated patch modification for tampering analysis", fill=(100, 100, 100))

    img.save(file_path, format="PNG")
    return file_path


def generate_sample_06_low_quality(output_dir: Path) -> Path:
    """Sample 06: Low quality scan simulation with small light gray text and noise."""
    file_path = output_dir / "sample_06_low_quality.pdf"
    pdf = TrustLensPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.draw_watermark()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 8, "ARCHIVAL COPY - LOW CONTRAST FACSIMILE TRANSMISSION", ln=True, align="C")
    pdf.ln(5)

    # Low contrast, small, hard-to-read text simulating degraded scanner
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(195, 195, 195)

    noisy_lines = [
        "Institution  N a m e :   [illegible]   Engineering   College",
        "A p p l i c a t i o n   N o :   A I C T E - 2 0 2 4 - L Q - 0 0 6",
        "A d d r e s s :   . . .   F a d e d   T e c h   Z o n e ,   P u n e",
        "D i r e c t o r :   D r .   [ u n r e a d a b l e ]",
        "P h o n e :   + 9 1 - 9 8 . . . . . . .",
        "T o t a l   I n t a k e :   [ s m u d g e d ]",
    ]

    for line in noisy_lines:
        pdf.cell(0, 6, line, ln=True)

    # Add visual noise dots across page
    pdf.set_draw_color(220, 220, 220)
    for i in range(15):
        y_pos = 60 + (i * 10)
        pdf.line(15, y_pos, 195, y_pos)

    pdf.output(str(file_path))
    return file_path


def calculate_sha256(file_path: Path) -> str:
    """Helper to compute SHA-256 checksum."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    samples_dir = base_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("TrustLens MVP - Generating Synthetic Test Documents")
    print(f"Target Directory: {samples_dir}")
    print("=================================================================\n")

    created_files = []

    # 1. Complete PDF
    f1 = generate_sample_01(samples_dir)
    created_files.append((f1, "Complete consistent application document"))

    # 2. Mismatch Pair (02a and 02b)
    f2a = generate_sample_02a(samples_dir)
    f2b = generate_sample_02b(samples_dir)
    created_files.append((f2a, "Cross-doc mismatch pair (Doc A: ABC Technical Institute)"))
    created_files.append((f2b, "Cross-doc mismatch pair (Doc B: XYZ Technology College, Same App No)"))

    # 3. Missing Fields PDF
    f3 = generate_sample_03(samples_dir)
    created_files.append((f3, "Missing mandatory fields (No name, address, email, director)"))

    # 4. Exact Duplicate PNGs
    f4a, f4b = generate_sample_04_duplicates(samples_dir)
    created_files.append((f4a, "Duplicate test image A (Affiliation Certificate)"))
    created_files.append((f4b, "Duplicate test image B (Bitwise SHA-256 identical to 4a)"))

    # 5. Visually Altered PNG
    f5 = generate_sample_05_altered(samples_dir)
    created_files.append((f5, "Altered document image with whiteout patch"))

    # 6. Low Quality PDF
    f6 = generate_sample_06_low_quality(samples_dir)
    created_files.append((f6, "Low quality degraded scan with low contrast text and noise"))

    # Print summary of created files
    print("Created Synthetic Files:")
    for file_path, desc in created_files:
        size_kb = file_path.stat().st_size / 1024
        print(f"  [+] {file_path.name:<28} ({size_kb:>6.1f} KB) - {desc}")

    # Check SHA-256 for duplicate pair
    sha_4a = calculate_sha256(f4a)
    sha_4b = calculate_sha256(f4b)
    assert sha_4a == sha_4b, "Duplicate files must have identical SHA-256 hashes"

    print("\n-----------------------------------------------------------------")
    print("Verification of Bitwise Duplicate Pair (SHA-256):")
    print(f"  sample_04a_duplicate.png: {sha_4a}")
    print(f"  sample_04b_duplicate.png: {sha_4b}")
    print(f"  Hash Match Result: {'MATCH (Identical)' if sha_4a == sha_4b else 'MISMATCH'}")
    print("-----------------------------------------------------------------\n")

    # Expected outcomes checklist
    print("=================================================================")
    print("TEST CHECKLIST & EXPECTED SCRUTINY OUTCOMES")
    print("=================================================================")
    print("1. sample_01_complete.pdf:")
    print("   - All mandatory fields extracted with high confidence.")
    print("   - Compliance rules pass; Low advisory risk score (0-15%).")
    print()
    print("2. sample_02a_mismatch.pdf + sample_02b_mismatch.pdf:")
    print("   - Cross-Document Comparison engine flags 'CRITICAL_MISMATCH'.")
    print("   - Reason: Differing Institution Name for same Application No AICTE-2024-ABC-002.")
    print("   - Elevates application risk score.")
    print()
    print("3. sample_03_missing_fields.pdf:")
    print("   - Rule Engine flags 'MANDATORY_FIELDS_MISSING'.")
    print("   - Flags missing: Institution Name, Email, Address, Director.")
    print()
    print("4. sample_04a_duplicate.png + sample_04b_duplicate.png:")
    print("   - Exact duplicate detection triggers on SHA-256 hash collision.")
    print("   - Flags duplicate document upload within/across applications.")
    print()
    print("5. sample_05_altered.png:")
    print("   - Error-Level Analysis (ELA) / visual inspection flags irregular compression")
    print("     and high-contrast boundary artifact near land area text.")
    print("   - Advisory finding for officer manual review.")
    print()
    print("6. sample_06_low_quality.pdf:")
    print("   - OCR extraction triggers 'LOW_CONFIDENCE_WARNING' (<0.60).")
    print("   - Triggers advisory rule recommending physical verification or high-res resubmission.")
    print("=================================================================")
