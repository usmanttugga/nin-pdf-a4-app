from flask import Flask, render_template, request, send_file
import os
import tempfile
import pdfplumber
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

def crop_pdf_page(page):
    words = page.extract_words()
    if not words:
        return page.bbox
    x0 = min(w['x0'] for w in words)
    x1 = max(w['x1'] for w in words)
    top = min(w['top'] for w in words)
    bottom = max(w['bottom'] for w in words)
    return (x0, top, x1, bottom)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("pdfs")
        output_path = os.path.join(tempfile.gettempdir(), "final_a4.pdf")

        c = canvas.Canvas(output_path, pagesize=A4)
        a4_w, a4_h = A4

        positions = [
            (0, a4_h / 2),
            (a4_w / 2, a4_h / 2),
            (0, 0),
            (a4_w / 2, 0),
        ]

        for i, f in enumerate(files):
            with pdfplumber.open(f) as pdf:
                page = pdf.pages[0]
                bbox = crop_pdf_page(page)
                cropped = page.crop(bbox)

                img = cropped.to_image(resolution=200).original
                img_path = os.path.join(tempfile.gettempdir(), f"img{i}.png")
                img.save(img_path)

                img_w, img_h = img.size
                scale = min((a4_w/2) / img_w, (a4_h/2) / img_h)

                c.drawImage(
                    img_path,
                    positions[i][0] + 5,
                    positions[i][1] + 5,
                    width=img_w * scale,
                    height=img_h * scale
                )

        c.save()
        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
