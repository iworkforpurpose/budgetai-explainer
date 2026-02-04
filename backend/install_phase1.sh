#!/bin/bash

# Budget 2026 AI - Phase 1 Quick Install Script
# This installs only the dependencies needed for PDF loading

echo "======================================================"
echo "📦 Budget 2026 AI - Phase 1 Installation"
echo "======================================================"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version

echo ""
echo "📥 Installing Phase 1 dependencies..."
echo "   - PyMuPDF (PDF extraction - primary)"
echo "   - pdfplumber (PDF extraction - fallback)"
echo "   - pydantic (settings validation)"
echo "   - pydantic-settings (environment config)"
echo "   - python-dotenv (.env support)"
echo ""

# Install dependencies
pip install PyMuPDF==1.23.26 pdfplumber==0.10.4 python-dotenv==1.0.1 pydantic==2.6.1 pydantic-settings==2.1.0

echo ""
echo "======================================================"
echo "✅ Installation Complete!"
echo "======================================================"
echo ""
echo "🧪 Verifying installation..."

# Verify installations
python3 -c "import fitz; print('  ✓ PyMuPDF version:', fitz.__version__)" 2>/dev/null || echo "  ✗ PyMuPDF not found"
python3 -c "import pdfplumber; print('  ✓ pdfplumber installed')" 2>/dev/null || echo "  ✗ pdfplumber not found"
python3 -c "from pydantic_settings import BaseSettings; print('  ✓ pydantic-settings installed')" 2>/dev/null || echo "  ✗ pydantic-settings not found"
python3 -c "from dotenv import load_dotenv; print('  ✓ python-dotenv installed')" 2>/dev/null || echo "  ✗ python-dotenv not found"

echo ""
echo "======================================================"
echo "🚀 Ready to Test!"
echo "======================================================"
echo ""
echo "Run: python test_pdf_loader.py"
echo ""
