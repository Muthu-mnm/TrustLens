import os
import io
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Create a test SQLite database
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "test_trustlens.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables on startup and cleanup on completion."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def db():
    """Provide an isolated database session per test with automatic rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Provide a FastAPI TestClient with the test database session overridden."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def sample_pdf_path():
    """Create a synthetic PDF document with AICTE application text for testing."""
    tmp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(tmp_dir, "sample_aicte_application.pdf")

    # Generate synthetic PDF using PyMuPDF if available, or fallback to pure PDF bytes
    sample_text = (
        "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
        "Institution Name: ABC College of Engineering\n"
        "Application ID: APP-2024-9988\n"
        "Campus Address: 104 Sector 62 Institutional Area, Knowledge Park\n"
        "Director: Dr. Ramesh Kumar Sharma\n"
        "Phone: 9876543210\n"
        "Email: contact@abccollege.edu\n"
        "Affiliated to: State Technical University\n"
        "Total Intake: 420\n"
        "Established: 2005\n"
        "Pincode: 201301\n"
        "State: Uttar Pradesh\n"
        "Programs: Computer Science and Engineering, Mechanical\n"
    )

    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), sample_text, fontsize=11)
        doc.save(pdf_path)
        doc.close()
    except Exception:
        # Fallback raw PDF stream
        escaped_text = sample_text.replace("\n", "\\n")
        pdf_bytes = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length " + str(len(sample_text) + 50).encode() + b">>stream\n"
            b"BT /F1 10 Tf 50 750 Td (" + escaped_text.encode("latin1", "ignore") + b") Tj ET\nendstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\n"
            b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n340\n%%EOF"
        )
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

    yield pdf_path

    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass


@pytest.fixture(scope="session")
def sample_image_path():
    """Create a synthetic test image."""
    tmp_dir = tempfile.gettempdir()
    img_path = os.path.join(tmp_dir, "sample_stamp.jpg")

    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (200, 200), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 180, 180], outline=(30, 64, 175), width=3)
        draw.text((35, 90), "OFFICIAL SEAL", fill=(30, 64, 175))
        img.save(img_path, "JPEG", quality=95)
    except Exception:
        # Minimal dummy JPEG header bytes
        with open(img_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x08\x00\x08\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9")

    yield img_path

    if os.path.exists(img_path):
        try:
            os.remove(img_path)
        except Exception:
            pass


@pytest.fixture(scope="session")
def sample_incomplete_pdf_path():
    """Create a synthetic PDF document lacking mandatory fields to guarantee rule findings."""
    tmp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(tmp_dir, "sample_incomplete_doc.pdf")
    sample_text = (
        "ANNEXURE - DRAFT NOTES\n"
        "Meeting Minutes without institutional identity or registration data.\n"
        "Some observations and rough estimates.\n"
    )

    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), sample_text, fontsize=11)
        doc.save(pdf_path)
        doc.close()
    except Exception:
        pdf_bytes = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length 80>>stream\n"
            b"BT /F1 10 Tf 50 750 Td (Incomplete Annexure Without Mandatory Fields) Tj ET\nendstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\n"
            b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n340\n%%EOF"
        )
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

    yield pdf_path

    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass

