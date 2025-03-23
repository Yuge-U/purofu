from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import datetime
import csv
from io import StringIO
from flask import Response
from flask import render_template, make_response
from weasyprint import HTML
from flask import render_template_string, make_response
from urllib.parse import quote
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    content = db.Column(db.String(200))

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    number = db.Column(db.Integer)
    school = db.Column(db.String(100))
    notes = db.Column(db.Text)
    image_filename = db.Column(db.String(100))
    status = db.Column(db.String(10), default="在籍") 
    team = db.Column(db.String(100))  # チーム名を追加


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    event = db.Column(db.String(100))
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    status = db.Column(db.String(10))
    profile = db.relationship("Profile", backref="attendances")

    def __repr__(self):
        return f"{self.date} - {self.event}"


with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        content = request.form["content"]
        new_msg = Message(name=name, content=content)
        db.session.add(new_msg)
        db.session.commit()
        return redirect("/")

    messages = Message.query.order_by(Message.id.desc()).all()
    return render_template("index.html", messages=messages)

@app.route("/edit_message/<int:id>", methods=["GET", "POST"])
def edit_message(id):
    message = Message.query.get_or_404(id)
    if request.method == "POST":
        message.name = request.form["name"]
        message.content = request.form["content"]
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit_message.html", message=message)

@app.route("/delete_message/<int:id>")
def delete_message(id):
    message = Message.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/profile_login", methods=["GET", "POST"])
def profile_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "1234":
            session["authenticated"] = True
            return redirect(url_for("profile"))
        else:
            return render_template("profile_login.html", error="パスワードが違います")
    return render_template("profile_login.html")

@app.route("/profile")
def profile():
    if not session.get("authenticated"):
        return redirect(url_for("profile_login"))

    keyword = request.args.get("keyword", "")
    school_list = request.args.getlist("school")
    grade_list = request.args.getlist("grade")
    gender_list = request.args.getlist("gender")
    team_list = request.args.getlist("team")
    status_list = request.args.getlist("status")  # ← 追加

    sort = request.args.get("sort", "new")

    query = Profile.query
    if keyword:
        query = query.filter(Profile.name.contains(keyword))
    if school_list:
        query = query.filter(Profile.school.in_(school_list))
    if grade_list:
        grade_list = [int(g) for g in grade_list if g.isdigit()]
        if grade_list:
            query = query.filter(Profile.grade.in_(grade_list))
    if gender_list:
        query = query.filter(Profile.gender.in_(gender_list))
    if team_list:
        query = query.filter(Profile.team.in_(team_list))
    if status_list:
        query = query.filter(Profile.status.in_(status_list))  # ← ここ！

    # 並び替え
    if sort == "name_asc":
        query = query.order_by(Profile.name.asc())
    elif sort == "name_desc":
        query = query.order_by(Profile.name.desc())
    elif sort == "grade":
        query = query.order_by(Profile.grade.asc())
    else:
        query = query.order_by(Profile.id.desc())

    # フィルター用データ
    schools = sorted([s[0] for s in db.session.query(Profile.school).distinct().all() if s[0]])
    grades = sorted([g[0] for g in db.session.query(Profile.grade).distinct().all() if g[0] is not None])
    genders = sorted([g[0] for g in db.session.query(Profile.gender).distinct().all() if g[0]])
    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])

    profiles = query.all()
    return render_template(
        "profile.html",
        profiles=profiles,
        keyword=keyword,
        sort=sort,
        schools=schools,
        grades=grades,
        genders=genders,
        teams=[t for t in teams],
        selected_schools=school_list,
        selected_grades=grade_list,
        selected_genders=gender_list,
        selected_teams=team_list,
        selected_status=status_list  # ← これもテンプレートへ
    )

@app.route("/profile/new", methods=["GET", "POST"])
def profile_new():
    if request.method == "POST":
        team = request.form.get("team")
        school = request.form.get("school")
        name = request.form["name"]
        grade = request.form.get("grade")
        gender = request.form.get("gender")
        number = request.form.get("number")
        status = request.form.get("status")
        notes = request.form.get("notes")

        # ✅ チーム名と出身校
        team = request.form.get("team_custom") or request.form.get("team")
        school = request.form.get("school_custom") or request.form.get("school")

        image = request.files["image"]
        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_profile = Profile(
            name=name, grade=grade, gender=gender, number=number,
            team=team, school=school, notes=notes,
            image_filename=filename, status=status
        )
        db.session.add(new_profile)
        db.session.commit()
        return redirect(url_for("index"))

    # 既存のチーム・出身校一覧
    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])
    schools = sorted([s[0] for s in db.session.query(Profile.school).distinct().all() if s[0]])
    return render_template("profile_new.html", teams=teams, schools=schools)




@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_profile(id):
    profile = Profile.query.get_or_404(id)

    if request.method == "POST":
        team = request.form.get("team")
        school = request.form.get("school")
        profile.name = request.form["name"]
        profile.grade = request.form.get("grade")
        profile.gender = request.form.get("gender")
        profile.number = request.form.get("number")
        profile.status = request.form.get("status")
        profile.notes = request.form.get("notes")

        # ✅ チーム・出身校：新規優先
        profile.team = request.form.get("team_custom") or request.form.get("team")
        profile.school = request.form.get("school_custom") or request.form.get("school")

        image = request.files["image"]
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile.image_filename = filename

        db.session.commit()
        return redirect(url_for("profile"))

    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])
    schools = sorted([s[0] for s in db.session.query(Profile.school).distinct().all() if s[0]])
    return render_template("edit.html", profile=profile, teams=teams, schools=schools)


@app.route("/attendance/mark", methods=["GET", "POST"])
def mark_attendance():
    events = Attendance.query.with_entities(Attendance.date, Attendance.event).distinct().all()
    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])
    selected_teams = request.args.getlist("team")

    if request.method == "POST":
        selected_date = request.form.get("date")
        selected_event = request.form.get("event")
        Attendance.query.filter_by(date=selected_date, event=selected_event).delete()

        for profile in Profile.query.all():
            if selected_teams and profile.team not in selected_teams:
                continue  # 選ばれていないチームはスキップ

            status = request.form.get(f"status_{profile.id}")
            new_record = Attendance(
                date=selected_date,
                event=selected_event,
                profile_id=profile.id,
                status=status
            )
            db.session.add(new_record)

        db.session.commit()
        return redirect(url_for("profile"))

    # フィルターして表示するプロフィール一覧
    profiles = Profile.query
    if selected_teams:
        profiles = profiles.filter(Profile.team.in_(selected_teams))

    profiles = profiles.order_by(Profile.grade.asc(), Profile.name.asc()).all()

    return render_template("attendance_mark.html",
        profiles=profiles,
        events=events,
        teams=teams,
        selected_teams=selected_teams
    )



@app.route("/attendance/new", methods=["GET", "POST"])
def attendance_new():
    selected_teams = request.args.getlist("team")
    profiles_query = Profile.query

    if selected_teams:
        profiles_query = profiles_query.filter(Profile.team.in_(selected_teams))

    profiles = profiles_query.order_by(Profile.grade.asc(), Profile.name.asc()).all()
    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])

    if request.method == "POST":
        date = request.form.get("date")
        event = request.form.get("event")

        # 重複チェック
        exists = Attendance.query.filter_by(date=date, event=event).first()
        if exists:
            return render_template("attendance_new.html",
                error="すでに登録済みの出欠があります",
                profiles=profiles,
                teams=teams,
                selected_teams=selected_teams
            )

        for profile in profiles:
            new_att = Attendance(date=date, event=event, profile_id=profile.id, status="")
            db.session.add(new_att)

        db.session.commit()
        return redirect(url_for("view_attendance", date=date, event=event))

    return render_template("attendance_new.html", profiles=profiles, teams=teams, selected_teams=selected_teams)




@app.route("/attendance/view", methods=["GET", "POST"])
def view_attendance():
    selected_date = request.args.get("date", "")
    selected_event = request.args.get("event", "")
    school = request.args.getlist("school")
    grade = request.args.getlist("grade")
    gender = request.args.getlist("gender")
    team = request.args.getlist("team")

    # ✅ POST: 出欠情報を保存する
    if request.method == "POST":
        for key, value in request.form.items():
            if key.startswith("status_"):
                profile_id = int(key.split("_")[1])
                attendance = Attendance.query.filter_by(
                    date=selected_date,
                    event=selected_event,
                    profile_id=profile_id
                ).first()
                if not attendance:
                    attendance = Attendance(date=selected_date, event=selected_event, profile_id=profile_id)
                attendance.status = value
                db.session.add(attendance)
        db.session.commit()
        flash("出欠情報を保存しました")
        return redirect(url_for("view_attendance", date=selected_date, event=selected_event))

    # ✅ GET: 出欠状況を表示する
    events = db.session.query(Attendance.date, Attendance.event).distinct().order_by(Attendance.date).all()

    query = Attendance.query.join(Profile)

    if selected_date and selected_event:
        query = query.filter(Attendance.date == selected_date, Attendance.event == selected_event)
    if school:
        query = query.filter(Profile.school.in_(school))
    if grade:
        query = query.filter(Profile.grade.in_(grade))
    if gender:
        query = query.filter(Profile.gender.in_(gender))
    if team:
        query = query.filter(Profile.team.in_(team))  # ← チームでフィルター！

    records = query.order_by(Profile.grade.asc(), Profile.name.asc()).all()

    teams = sorted([t[0] for t in db.session.query(Profile.team).distinct().all() if t[0]])
    return render_template("attendance_view.html",
    records=records,
    events=events,
    selected_date=selected_date,
    selected_event=selected_event,
    schools=db.session.query(Profile.school).distinct().order_by(Profile.school).all(),
    grades=db.session.query(Profile.grade).distinct().order_by(Profile.grade).all(),
    genders=db.session.query(Profile.gender).distinct().order_by(Profile.gender).all(),
    teams=teams,                     # ✅ 定義したteamsをここで使う
    selected_teams=team             # ✅ 選択されたチーム名（リスト）
)


# -------------------------
# 出欠イベント登録
# -------------------------
@app.route("/attendance/register", methods=["GET", "POST"])
def register_attendance_event():
    selected_teams = request.args.getlist("team")

    # 🔹 フィルターされたプロフィールのみ取得
    query = Profile.query
    if selected_teams:
        query = query.filter(Profile.team.in_(selected_teams))
    profiles = query.all()

    # 🔹 イベント名の候補一覧（distinct）
    existing_events = sorted(set(
        [e[0] for e in db.session.query(Attendance.event).distinct() if e[0]]
    ))

    if request.method == "POST":
        date = request.form.get("date")
        event = request.form.get("event")

        if not date or not event:
            return render_template("attendance_register.html",
                                   error="日付とイベント名は必須です。",
                                   profiles=profiles,
                                   selected_teams=selected_teams,
                                   teams=[t[0] for t in db.session.query(Profile.team).distinct()],
                                   existing_events=existing_events)

        # 重複チェック
        exists = Attendance.query.filter_by(date=date, event=event).first()
        if exists:
            return render_template("attendance_register.html",
                                   error="同じ日付・イベント名の出欠記録が既に存在します。",
                                   profiles=profiles,
                                   selected_teams=selected_teams,
                                   teams=[t[0] for t in db.session.query(Profile.team).distinct()],
                                   existing_events=existing_events)

        # 出欠レコード作成
        for profile in profiles:
            record = Attendance(date=date, event=event, profile_id=profile.id, status="")
            db.session.add(record)
        db.session.commit()

        flash("出欠イベントを作成しました")
        return redirect(url_for("view_attendance", date=date, event=event))

    # 🔹 GETリクエストのとき
    teams = [t[0] for t in db.session.query(Profile.team).distinct() if t[0]]

    return render_template("attendance_register.html",
                           profiles=profiles,
                           teams=teams,
                           selected_teams=selected_teams,
                           existing_events=existing_events)



@app.route("/attendance/export_csv")
def export_attendance_csv():
    date = request.args.get("date")
    event = request.args.get("event")
    teams = request.args.getlist("team")

    if not date or not event:
        return "日付とイベント名が必要です", 400

    query = (
        db.session.query(Profile, Attendance)
        .join(Attendance, Profile.id == Attendance.profile_id)
        .filter(Attendance.date == date, Attendance.event == event)
    )

    if teams:
        query = query.filter(Profile.team.in_(teams))

    records = query.order_by(Profile.grade.asc(), Profile.name.asc()).all()

    si = StringIO()
    si.write('\ufeff')  # UTF-8 BOM
    writer = csv.writer(si)
    writer.writerow(["チーム","名前", "学年", "性別", "チーム", "出身校", "出席ステータス"])
    for profile, attendance in records:
        writer.writerow([profile.team,profile.name, profile.grade, profile.gender, profile.team, profile.school, attendance.status])

    filename = f"attendance_{date}_{event}.csv"
    encoded_filename = quote(filename)

    return Response(
        si.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )


@app.route("/attendance/export_pdf")
def export_attendance_pdf():
    date = request.args.get("date")
    event = request.args.get("event")
    teams = request.args.getlist("team")

    if not date or not event:
        return "日付とイベント名が必要です", 400

    query = (
        db.session.query(Profile, Attendance)
        .join(Attendance, Profile.id == Attendance.profile_id)
        .filter(Attendance.date == date, Attendance.event == event)
    )

    if teams:
        query = query.filter(Profile.team.in_(teams))

    records = query.order_by(Profile.grade.asc(), Profile.name.asc()).all()

    html = render_template("attendance_pdf.html", records=records, date=date, event=event)
    pdf = HTML(string=html).write_pdf()

    filename = f"attendance_{date}_{event}.pdf"
    encoded_filename = quote(filename)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    return response

@app.route("/profile/import_csv", methods=["GET", "POST"])
def import_profile_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("ファイルが選択されていません", "danger")
            return redirect(url_for("profile"))

        import csv
        import codecs
        stream = codecs.iterdecode(file.stream, 'utf-8-sig')  # UTF-8 BOM対応
        reader = csv.DictReader(stream)

        count = 0
        for row in reader:
            profile = Profile(
                name=row.get("名前", ""),
                grade=row.get("学年"),
                gender=row.get("性別"),
                number=row.get("背番号"),
                school=row.get("出身校"),
                team=row.get("チーム名"),
                status=row.get("ステータス", "在籍"),
                notes=row.get("備考"),
                image_filename=row.get("画像ファイル名")  # あくまで名前だけ保存（画像は対象外）
            )
            db.session.add(profile)
            count += 1

        db.session.commit()
        flash(f"{count} 件のプロフィールをインポートしました", "success")
        return redirect(url_for("profile"))

    return render_template("import_csv.html")

from io import StringIO
import csv

@app.route("/download_sample_csv")
def download_sample_csv():
    si = StringIO()
    si.write('\ufeff')  # UTF-8 BOM を追加（Excelで文字化け防止）

    writer = csv.writer(si)
    writer.writerow(["name", "grade", "gender", "number", "team", "school", "notes", "status"])
    writer.writerow(["山田太郎", 3, "男性", 10, "レッドチーム", "第一小学校", "キャプテン", "在籍"])
    writer.writerow(["佐藤花子", 2, "女性", 11, "ブルーチーム", "第二小学校", "", "在籍"])
    writer.writerow(["田中一郎", 1, "男性", 9, "イエローチーム", "第三小学校", "メモあり", "退団"])

    response = Response(si.getvalue(), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=sample_profiles.csv"
    return response

@app.route("/profile/export_csv")
def export_profile_csv():
    import csv
    from io import StringIO
    from urllib.parse import quote
    from flask import Response

    profiles = Profile.query.order_by(Profile.id).all()

    si = StringIO()
    si.write('\ufeff')  # UTF-8 BOM for Excel compatibility
    writer = csv.writer(si)
    writer.writerow([
        "名前", "学年", "性別", "背番号", "出身校", "チーム名", "ステータス", "備考", "画像ファイル名"
    ])

    for p in profiles:
        writer.writerow([
            p.name,
            p.grade,
            p.gender,
            p.number,
            p.school,
            p.team,
            p.status,
            p.notes,
            p.image_filename or ""
        ])

    filename = quote("profile_backup.csv")
    return Response(
        si.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


@app.route("/delete/<int:id>")
def delete_profile(id):
    profile = Profile.query.get_or_404(id)
    db.session.delete(profile)
    db.session.commit()
    return redirect(url_for("profile"))

app = Flask(__name__)

if __name__ == "__main__":
    app.run()
