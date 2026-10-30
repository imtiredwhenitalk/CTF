from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import products
from .challenge import sanitize_review
from .db import get_db

bp = Blueprint("shop", __name__)


@bp.route("/")
def index():
    return render_template("index.html", products=products.get_all())


@bp.route("/product/<int:product_id>")
def product(product_id):
    item = products.get_by_id(product_id)
    if item is None:
        abort(404)
    reviews = get_db().execute(
        "SELECT author, body, created_at FROM reviews WHERE product_id = ? ORDER BY id DESC",
        (product_id,),
    ).fetchall()
    return render_template("product.html", product=item, reviews=reviews)


@bp.route("/product/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    if products.get_by_id(product_id) is None:
        abort(404)

    author = request.form.get("author", "").strip()[:40] or "Анонім"
    body = request.form.get("body", "").strip()[:1000]
    if body:
        db = get_db()
        db.execute(
            "INSERT INTO reviews (product_id, author, body) VALUES (?, ?, ?)",
            (product_id, author, sanitize_review(body)),
        )
        db.commit()
    return redirect(url_for("shop.product", product_id=product_id))


@bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    found = products.search(query) if query else []
    return render_template("search.html", query=query, products=found)


@bp.app_errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404
