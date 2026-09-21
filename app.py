from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ophthalmic")
def ophthalmic():
    return render_template("subjects/ophthalmic.html")


@app.route("/ent")
def ent():
    return render_template("subjects/ent.html")


@app.route("/oncology")
def oncology():
    return render_template("subjects/oncology.html")


@app.route("/emergency")
def emergency():
    return render_template("subjects/emergency.html")


@app.route("/research")
def research():
    return render_template("subjects/research.html")


@app.route("/leadership1")
def leadership1():
    return render_template("subjects/leadership1.html")


@app.route("/leadership2")
def leadership2():
    return render_template("subjects/leadership2.html")


@app.route("/curriculum")
def curriculum():
    return render_template("subjects/curriculum.html")


@app.route("/theatre")
def theatre():
    return render_template("subjects/theatre.html")


if __name__ == "__main__":
    app.run(debug=True)