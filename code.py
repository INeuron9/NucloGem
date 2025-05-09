#!/usr/bin/env python3
"""
🔍 Nuclei + Gemini Scanner & Reporter for Kali Linux
"""

import os
import subprocess
import json
from datetime import datetime
import google.generativeai as genai

# ----- CONFIG -----
NUCLEI_PATH = "nuclei"
TEMPLATES_DIR = os.path.expanduser("~/nuclei-templates")
OUTPUT_DIR = "nuclei_scans"
GEMINI_API_KEY = "gemini_api_key_here"  # Replace with yours
REPORT_PATH = os.path.expanduser("~/Desktop/gemini_report")
# -------------------

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def verify_setup():
    """Ensure required tools and templates exist"""
    print("📦 Verifying Nuclei and template setup...")
    try:
        subprocess.run([NUCLEI_PATH, "-version"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except:
        print("❌ Nuclei not found. Install with:")
        print("go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest")
        exit(1)

    if not os.path.exists(TEMPLATES_DIR):
        print(f"❌ Templates not found at {TEMPLATES_DIR}")
        print("Update templates using: nuclei -update-templates")
        exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("✅ Setup verified.\n")

def run_nuclei_scan(target):
    """Run Nuclei scan on the given target"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"scan_{timestamp}.json")

    cmd = [
        NUCLEI_PATH,
        "-u", target,
        "-t", TEMPLATES_DIR,  # Run all templates
        "-silent",
        "-o", output_file
    ]

    print(f"🚀 Running Nuclei scan on {target} using all templates...")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Scan completed. Results saved to {output_file}\n")
        return output_file
    except subprocess.CalledProcessError:
        print("❌ Scan failed. Check internet or target URL format (http:// or https://)")
        exit(1)

def generate_report_from_file(file_path):
    """Use Gemini to analyze the scan results and create a Markdown report"""
    print("🤖 Sending results to Gemini for analysis...")
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"

    prompt = f"""
    Analyze the following Nuclei scan output and generate a detailed, structured security report in Markdown format.
    Highlight critical and high-severity issues. Use proper headings and bullet points.

    --- Begin Scan Data ---
    {content}
    --- End Scan Data ---
    """

    try:
        response = model.generate_content(prompt)
        print("✅ Gemini analysis complete.\n")
        return response.text.strip()
    except Exception as e:
        return f"Error communicating with Gemini: {e}"

def save_report_to_pdf(markdown_text, base_path):
    """Save Markdown and convert to PDF"""
    md_path = base_path + ".md"
    pdf_path = base_path + ".pdf"

    print("📝 Saving Markdown report...")
    with open(md_path, "w") as f:
        f.write(markdown_text)

    print("📄 Converting Markdown to PDF...")
    try:
        subprocess.run(["pandoc", md_path, "-o", pdf_path], check=True)
        os.remove(md_path)
        print(f"✅ PDF report saved at: {pdf_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to convert to PDF: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nuclei + Gemini Automated Scanner")
    parser.add_argument("target", help="Target URL (include http:// or https://)")
    args = parser.parse_args()

    verify_setup()
    scan_file = run_nuclei_scan(args.target)
    report_md = generate_report_from_file(scan_file)

    if "Error" in report_md:
        print(report_md)
    else:
        save_report_to_pdf(report_md, REPORT_PATH)
