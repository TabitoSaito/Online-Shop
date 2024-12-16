import os
from dotenv import load_dotenv
from flask import Flask, redirect, request, render_template, url_for
import stripe
from flask_bootstrap import Bootstrap5
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from forms import CreateForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String

load_dotenv()

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")


stripe.api_key = API_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

bootstrap = Bootstrap5(app)

YOUR_DOMAIN = 'http://localhost:4242'


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Item(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[str] = mapped_column(String(250), nullable=False)
    price_id: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)


with app.app_context():
    db.create_all()


def cut_list(origin_list: list) -> list:
    deduction = len(origin_list) % 3

    processed_list = []

    if deduction == 0:
        pairs = int(len(origin_list) / 3)
    else:
        pairs = int(len(origin_list[:-deduction]) / 3)

    for i in range(0, pairs):
        test = []
        for j in range(0, 3):
            test.append(origin_list[i * 3 + j])
        processed_list.append(test)

    if deduction != 0:
        processed_list.append(origin_list[-deduction:])

    return processed_list


@app.route("/")
def home():
    result = db.session.execute(db.select(Item))
    product_list = result.scalars().all()
    product_list_processed = cut_list(product_list)
    return render_template("index.html", products=product_list_processed)


@app.route("/add", methods=["POST", "GET"])
def add_product():
    form = CreateForm()
    if form.validate_on_submit():
        name: str = form.data.get("name")
        img_url: str = form.data.get("img_url")
        price: str = form.data.get("price")

        try:
            price: float = float(price)
        except ValueError:
            price = price.replace(",", ".")
            price: float = float(price)

        price: str = format(price, ".2f")

        stripe_price = int(price.replace(".", ""))

        product = stripe.Product.create(name=name)

        stripe_price = stripe.Price.create(product=product.stripe_id,
                                           unit_amount=stripe_price,
                                           currency="usd",
                                           )
        price_id = stripe_price.stripe_id

        if db.session.execute(db.select(Item).where(Item.name == name)).scalar() is None:
            item = Item(
                name=name,
                img_url=img_url,
                price=price,
                price_id=price_id
            )

            db.session.add(item)
            db.session.commit()
            return redirect(url_for("home"))

    return render_template("Form.html", form=form)


@app.route('/create-checkout-session', methods=['POST', "GET"])
def create_checkout_session():
    name = request.args.get("name")

    item = db.session.execute(db.select(Item).where(Item.name == name)).scalar()

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': item.price_id,
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


if __name__ == '__main__':
    app.run(port=4242, debug=True)
