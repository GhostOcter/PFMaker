from flask import Flask, url_for, redirect, render_template, request, session
import json

app = Flask(__name__)
app.secret_key = "Je m'enfous de la sécurité"
supported_languages = ["Python", "Rust", "JS", "PHP", "C++", "C"]

@app.route("/", methods = ["POST", "GET"])
def home(): 
    if request.method == "POST":
        search = request.form["search"] if request.form["search"] != "" else "ALL"
        return redirect(url_for("search", search = search, search_type = request.form["search_type"]))
    else:
        return render_template(
            "home.html",
            is_login = True if "user" in session else False, 
            is_home = True
        )

@app.route("/search/<search>/<search_type>")
def search(search, search_type):
    result_users = []
    if search != "ALL":
        if search_type == "language":
            users = json.load(open("data/users.json", "r"))
            result_users = {}
            for user in users:
                user_stats = json.load(open("data/" + user + ".json"))["statistics"]["languages"]
                for language in user_stats:
                    if search.lower() == language.lower():
                        if user_stats[language] > 0:
                            result_users[user] = user_stats[language]
                        break
            result_users = [user[0] for user in sorted(result_users.items(), key = lambda x: x[1])]
        else:
            users = json.load(open("data/users.json", "r"))
            for user in users:
                if search in user:
                    result_users.append(user)
    else:
        result_users = json.load(open("data/users.json", "r")).keys()
    return render_template("search_result.html", is_login = True, result_users = result_users)

@app.route("/profile/<user>/summary/")
def summary(user):
    stats = json.load(open("data/" + user + ".json", "r"))["statistics"]
    percent_stats = {}
    for language in stats["languages"]:
        percent_stats[language] = round(stats["languages"][language] / stats["total"] * 100, 0)
    return render_template(
        "summary.html",
        is_login = True if "user" in session else False,
        is_profile = True,
        summary_content = json.load(open("data/" + user + ".json", "r"))["summary"],
        percent_stats = percent_stats,
        additional_navbar = True,
        user = user
    )

@app.route("/profile/<user>/projects/")
def projects(user):
    return render_template(
        "projects.html",
        is_login = True if "user" in session else False,
        is_profile = True,
        user = user,
        projects = json.load(open("data/" + user + ".json"))["projects"]
    )

@app.route("/your_summary/", methods = ["POST", "GET"])
def your_summary():
    if request.method == "POST":
        user_data = json.load(open("data/" + session["user"] + ".json"))
        user_data["summary"] = request.form["summary"]
        json.dump(user_data, open("data/" + session["user"] + ".json", "w"))
        return redirect(url_for("your_summary"))
    else:
        return render_template("your_summary.html", 
        is_login = True if "user" in session else False,
        summary_content = json.load(open("data/" + session["user"] + ".json"))["summary"]
        )

@app.route("/your_projects/")
def your_projects():
    return render_template(
        "your_projects.html",
        is_login = True if "user" in session else False,
        projects = json.load(open("data/" + session["user"] + ".json", "r"))["projects"]
        )

@app.route("/add_project/", methods = ["POST", "GET"])
def add_project():
    if request.method == "POST":
        save_project(request.form["project_name"], request.form["project_link"], request.form["project_language"], request.form["project_description"])
        return redirect(url_for("your_projects"))
    else:
        languages = {}
        for language in supported_languages:
            languages[language] = True if language == "Python" else False 
        print(languages)
        return render_template(
            "edit_project.html",
            is_login = True if "user" in session else False,
            project_name = "",
            project_link = "",
            project_languages = languages,
            project_description = ""
        )

@app.route("/edit_project/<project_name>", methods = ["POST", "GET"])
def edit_project(project_name):
    if request.method == "POST":
        save_project(request.form["project_name"], request.form["project_link"], request.form["project_language"], request.form["project_description"])
        return redirect(url_for("your_projects"))
    else:
        project = json.load(open("data/" + session["user"] + ".json"))["projects"][project_name]
        return render_template(
            "edit_project.html",
            is_login = True if "user" in session else False,
            project_name = project_name,
            project_link = project["link"],
            project_languages = project["languages"],
            project_description = project["description"]
        )

@app.route("/profile/<user>/projects/<project_name>")
def view_project(user, project_name):
    project = json.load(open("data/" + user + ".json"))["projects"][project_name]
    return render_template(
        "view_project.html",
        is_login = True if "user" in session else False,
        is_profile = True,
        user = user,
        project_name = project_name,
        project_link = project["link"],
        project_language = list(project["languages"].keys())[list(project["languages"].values()).index(True)],
        project_description = project["description"]
    )

def save_project(project_name, project_link, project_language, project_description):
    languages = {}
    print(project_language)
    for language in supported_languages:
        languages[language] = True if language == project_language else False
    user_data = json.load(open("data/" + session["user"] + ".json"))
    user_data["projects"][project_name] = {
        "link": project_link,
        "languages": languages,
        "description": project_description
    }
    user_data["statistics"]["total"] += 1
    user_data["statistics"]["languages"][project_language] += 1
    json.dump(user_data, open("data/" + session["user"] + ".json", "w"))

@app.route("/register/", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        users_data = json.load(open("data/users.json", "r"))
        if not username in users_data.keys():
            users_data[username] = request.form["password"]
            json.dump(users_data, open("data/users.json", "w"))
        session["user"] = username
        stats = {}
        stats["languages"] =  {language: 0 for language in supported_languages}
        stats["total"] = 0
        json.dump({"summary":"", "projects":{}, "statistics": stats}, open("data/" + username + ".json", "w"))
        return redirect(url_for("home"))
    else:
        return render_template("register_login.html", is_login = False)

@app.route("/login/", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        users_data = json.load(open("data/users.json", "r"))
        if username in users_data.keys() and users_data[username] == request.form["password"]:
            session["user"]  = username
        return redirect(url_for("home"))
    else:
        return render_template("register_login.html", is_login = False)

@app.route("/logout/")
def logout():
    if "user" in session:
        session.pop("user")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug = False)