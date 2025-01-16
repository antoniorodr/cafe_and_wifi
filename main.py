from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import random
import os

app = Flask(__name__)
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
Bootstrap5(app)

class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/random")
def random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())

@app.route("/all")
def all_cafe():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])

@app.route("/search/")
def search_cafe():
    query_location = request.args.get("loc")
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404

@app.route("/add", methods = ["POST"])
def new_cafe():
    name = request.form.get("name")
    existing_cafe = db.session.query(Cafe).filter_by(name=name).first()
    if existing_cafe:
        return jsonify(error={"message": "A cafe with this name already exists."}), 400

    new_cafe = Cafe(
        name=name,
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        has_sockets=request.form.get("sockets") == 'True',
        has_toilet=request.form.get("toilet") == 'True',
        has_wifi=request.form.get("wifi") == 'True',
        can_take_calls=request.form.get("calls") == 'True',
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )

    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


@app.route("/update/<cafe_id>", methods = ["PATCH"])
def update(cafe_id):
    new_price = request.args.get("coffee_price")
    result = db.get_or_404(Cafe, cafe_id)
    if result:
        result.coffee_price = f"£{new_price}"
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."}), 200
    else:
        return jsonify(error={"Not Found": "Sorry, a cafe with that ID was not found in the database."}), 404

@app.route("/delete/<cafe_id>", methods=["DELETE"])
def delete(cafe_id):
    cafe_to_delete = db.session.get(Cafe, cafe_id)
    api_key = request.headers.get("api-key")
    if cafe_to_delete is None:
        return jsonify(error={"Not Found": "Sorry, a cafe with that ID was not found in the database."}), 404
    if api_key != os.environ["api-key"]:
        return jsonify({"Error": "Sorry, that's not allowed. Make sure you have the right api_key."}), 403
    else:
        db.session.delete(cafe_to_delete)
        db.session.commit()
        return jsonify({"success": "The cafe with the id indicated has been deleted."}), 200

if __name__ == '__main__':
    app.run(debug=True)
