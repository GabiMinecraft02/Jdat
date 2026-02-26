from flask import Flask, render_template, send_from_directory, abort
import os

app = Flask(__name__)

# ── Routes principales ─────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", lang="fr")

@app.route("/en")
def index_en():
    return render_template("index.html", lang="en")

@app.route("/docs")
def docs_fr():
    return render_template("docs.html", lang="fr")

@app.route("/en/docs")
def docs_en():
    return render_template("docs.html", lang="en")

@app.route("/download")
def download_fr():
    return render_template("download.html", lang="fr")

@app.route("/en/download")
def download_en():
    return render_template("download.html", lang="en")

# ── Téléchargement des fichiers ────────────────────────────
@app.route("/files/<path:filename>")
def serve_file(filename):
    files_dir = os.path.join(app.root_path, "files")
    if not os.path.exists(os.path.join(files_dir, filename)):
        abort(404)
    return send_from_directory(files_dir, filename, as_attachment=True)

# ── SEO ────────────────────────────────────────────────────
@app.route("/robots.txt")
def robots():
    return send_from_directory(".", "robots.txt")

@app.route("/sitemap.xml")
def robots():
    return send_from_directory(".", "sitemap.xml")

@app.route("/googlea128813747473c36.html")
def robots():
    return send_from_directory(".", "googlea128813747473c36.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
