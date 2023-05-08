from flask import Flask, url_for
from flask import render_template
from flask import request, redirect
from flask_login import login_required, UserMixin, LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import pandas as pd
import os
import datetime
from sqlalchemy import Index

current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "blog.db")
app.config['SECRET_KEY'] = '3874jhjhgjh23jhgj13b4hgvfhgf'

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
app.app_context().push()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(db.String)
    user_posts = db.relationship('Posts', backref="author", cascade="all, delete")
    Index("idx_user_username", username)

class Posts(db.Model):
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    post_title = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    image_url = db.Column(db.String)
    post_created_ts = db.Column(db.DateTime, nullable=False)
    likes = db.Column(db.Integer)
    dislikes = db.Column(db.Integer)
    user_no = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_updated_ts = db.Column(db.DateTime)
    post_comments = db.relationship('Comments', backref='post', cascade="all, delete")


class Followers(db.Model):
    __tablename__ = 'followers'
    user_no = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    following_user = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Comments(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    comment_text = db.Column(db.String)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'))
    user_name = db.Column(db.String, db.ForeignKey('user.username'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def home():
    # db.create_all()
    if request.method == 'GET':
        print(datetime.datetime.now())
        return render_template("login.html")
    elif request.method == 'POST':
        user_name = request.form["username"]
        pwd = request.form["password"]
        user1 = User.query.filter(User.username == user_name).first()
        if not user1 or not check_password_hash(user1.password, pwd):
            return render_template("login.html", message='Incorrect Username or password !!!', user=user_name)
        else:
            login_user(user1, remember=True)
            return redirect(url_for('welcome', user_no=user1.id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    print('login: ', request.method)
    if request.method == 'GET':
        print(datetime.datetime.now())
        return render_template("login.html")


def validate_email(email):
    valid = True
    idx1 = 0
    idx2 = 0
    if '@' in email:
        idx1 = email.index('@')
        if email[0] == '@' or email[-1] == '@':
            valid = False
        else:
            valid = True
    if valid and '.' in email:
        idx2 = email.index('.')
        if email[0] == '.' or email[-1] == '.':
            valid = False
        else:
            valid = True
    if valid:
        if(abs(idx1-idx2) <=1 ):
            valid = False
        else:
            valid = True
    return valid

def validate_input(user_input):
    errmsg = ''
    user1 = User.query.filter(User.username == user_input['username']).first()
    if (user1):
        valid = False
        errmsg = 'User Name alredy exists. Please use different Username'
        return valid, errmsg
    user1 = User.query.filter(User.email == user_input['email']).first()
    if (user1):
        valid = False
        errmsg = 'Email already exists. Please use different email'
        return valid, errmsg
    if (validate_email(user_input['email'])):
        valid = True
    else:
        valid = False
        errmsg = 'Please enter a valid email'
        return valid, errmsg
    print('password length: ', len(user_input['pwd']))
    if (len(user_input['pwd']) < 8):
        valid = False
        errmsg = "Password should be minimum 8 characters"
        return valid, errmsg
    if (user_input['pwd'] != user_input['repwd']):
        valid = False
        errmsg = 'Passwords are not matching'
        return valid, errmsg
    return valid, errmsg

@app.route('/register', methods=['GET', 'POST'])
def register():
    print('register user...')
    if request.method == 'GET':
        user_input = {}
        user_input['username'] = ''
        user_input['email'] = ''
        user_input['pwd'] = ''
        user_input['repwd'] = ''
        return render_template("register_user.html", message='', user=user_input)
    elif request.method == 'POST':
        user_name = request.form["username"]
        pwd = request.form["password"]
        repwd = request.form["repassword"]
        email = request.form["email"]
        img_name = request.form["img_name"]
        user_input = {}
        user_input['username'] = user_name
        user_input['email'] = email
        user_input['pwd'] = pwd
        user_input['repwd'] = repwd

        valid, errmsg = validate_input(user_input)
        if (valid):
            password = generate_password_hash(pwd, method='md5')
            new_user = User(username=user_name, password=password, email=email, profile_image=img_name)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            return redirect(url_for('welcome', user_no=new_user.id))
        else:
            return render_template("register_user.html", message=errmsg, user=user_input)


@app.route('/update_user', methods=['GET', 'POST'])
@login_required
def update_user():
    if request.method == 'GET':
        user_input = {}
        user_input['username'] = current_user.username
        user_input['email'] = current_user.email
        user_input['pwd'] = current_user.password
        return render_template("update_user.html", user=user_input)
    elif request.method == 'POST':
        user_id = current_user.id
        user_name = current_user.username
        email = request.form["email"]
        img_name = request.form["img_name"]

        user_input = {}
        user_input['username'] = user_name
        user_input['email'] = email

        user1 = User.query.get(user_id)
        valid = validate_email(email)
        if user1 and valid:
            modified_user = User.query.get(user_id)
            modified_user.email = email
            modified_user.profile_image = img_name
            db.session.commit()
            return redirect(url_for('viewfeed'))
        else:
            errmsg = 'Please enter a valid email'
            return render_template('update_user.html', message=errmsg, user=user_input)

@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user():
    user_id = current_user.id
    curr_user = User.query.get(user_id)
    user_name = curr_user.username
    c1 = Comments.query.filter(Comments.user_name == user_name).all()
    print('comments from delete: ', c1)
    for c in c1:
        db.session.delete(c)
    follow1 = Followers.query.filter(Followers.user_no == user_id).all()
    for f in follow1:
        db.session.delete(f)
    follow2 = Followers.query.filter(Followers.following_user == user_id).all()
    for f in follow2:
        db.session.delete(f)
    db.session.delete(curr_user)
    db.session.commit()
    return redirect(url_for('logout'))


@app.route('/welcome', methods=['GET'])
@login_required
def welcome():
    print(current_user.username)
    user_id = current_user.id
    feed_list = Followers.query.filter(Followers.user_no == user_id).all()
    l = len(feed_list)
    if (l == 0):
        return render_template("welcome.html")
    else:
        return redirect(url_for('viewfeed'))


@app.route('/viewfeed', methods=['GET'])
@login_required
def viewfeed():
    user_id = current_user.id
    following_list = Followers.query.filter(Followers.user_no == user_id).all()
    post_list = []
    for item in following_list:
        list1 = Posts.query.filter(Posts.user_no == item.following_user).order_by(Posts.post_updated_ts.desc()).all()
        for l in list1:
            print('timestamp:', l.post_id, l.post_updated_ts)
            post_user = User.query.get(item.following_user)
            post_user_name = post_user.username
            comments = Comments.query.filter(Comments.post_id == l.post_id).all()
            print('comments: ', comments)
            post_list.append((l, post_user_name, comments))
    post_list.sort(key=lambda x:x[0].post_updated_ts, reverse=True)
    return render_template("feed.html", post_list=post_list)


@app.route('/profile_page/<int:prof_user>', methods=['GET'])
@login_required
def profile_page(prof_user):
    prof_user_name = User.query.get(prof_user).username
    img = User.query.get(prof_user).profile_image
    followers_list = Followers.query.filter(Followers.following_user == prof_user).all()
    following_list = Followers.query.filter(Followers.user_no == prof_user).all()
    c1 = len(following_list)
    c2 = len(followers_list)
    list1 = Posts.query.filter(Posts.user_no == prof_user).order_by(Posts.post_updated_ts.desc()).all()
    post_list = []
    for l in list1:
        comments = Comments.query.filter(Comments.post_id == l.post_id).all()
        print('comments: ', comments)
        post_list.append((l, comments))
    print('profile page:', list1)
    pct = len(list1)
    print('profile post count: ', pct, c1, c2)
    return render_template("profile.html", followers=c2, following=c1, post_list=post_list,
                           pct=pct, img=img, prof_user=prof_user_name)


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    user_id = current_user.id
    if request.method == 'GET':
        return render_template("add_post.html")
    elif request.method == 'POST':
        post_name = request.form["name"]
        desc = request.form["desc"]
        img_name = request.form["img_name"]
        print(img_name)
        img_path = '../static/' + img_name
        current_timestamp = datetime.datetime.now()
        new_post = Posts(post_title=post_name, description=desc, user_no=user_id, image_url=img_name,
                         post_created_ts=current_timestamp, post_updated_ts=current_timestamp, likes=0, dislikes=0)
        db.session.add(new_post)
        db.session.commit()
        feed_list = Followers.query.filter(Followers.user_no == user_id).all()
        l = len(feed_list)
        if (l == 0):
            return render_template("welcome.html")
        else:
            return redirect(url_for('profile_page',prof_user=user_id))


@app.route('/search_user', methods=['GET', 'POST'])
@login_required
def search_user():
    if request.method == 'GET':
        return render_template("search.html", l=-1)
    elif request.method == 'POST':
        name = request.form["search_user"]
        user = '%' + name + '%'
        print(('search for: ', user))
        srch_user = User.query.filter(User.username.like(user)).filter(User.id != current_user.id).order_by(User.username).all()
        print(srch_user)
        l = len(srch_user)
        return render_template("search.html", result=srch_user, l=l)


@app.route('/followers/<string:prof_user_name>', methods=['GET', 'POST'])
@login_required
def followers(prof_user_name):
    prof_user = User.query.filter(User.username == prof_user_name).first()
    print(request.method)
    if request.method == 'GET':
        followers_list = db.session.query(User).join(Followers, Followers.following_user == prof_user.id). \
            filter(Followers.user_no == User.id).all()
        l = len(followers_list)
        print(l, followers_list)
        return render_template("followers.html", l=l, followers=followers_list, prof_user_name=prof_user.username)


@app.route('/following/<string:prof_user_name>', methods=['GET', 'POST'])
@login_required
def following(prof_user_name):
    prof_user = User.query.filter(User.username == prof_user_name).first()
    print(request.method)
    if request.method == 'GET':
        following_list = db.session.query(User).join(Followers, Followers.following_user == User.id). \
            filter(Followers.user_no == prof_user.id).all()
        l = len(following_list)
        print(l, following_list)
        return render_template("following.html", l=l, followers=following_list, prof_user_name=prof_user.username)


@app.route('/follow/<int:follow_user>')
@login_required
def follow(follow_user):
    user_id = current_user.id
    print('Follow: ', user_id, follow_user)
    if(user_id != follow_user):
        temp = Followers.query.filter(Followers.following_user == follow_user).filter(Followers.user_no == user_id).first()
        print('current follow: ', temp)
        if(not temp):
            new_follow = Followers(user_no=user_id, following_user=follow_user)
            db.session.add(new_follow)
            db.session.commit()
    return redirect(url_for('profile_page',prof_user=user_id))


@app.route('/unfollow/<int:follow_user>')
@login_required
def unfollow(follow_user):
    user_id = current_user.id
    print('Unfollow: ', user_id, follow_user)
    follow1 = Followers.query.filter(Followers.following_user == follow_user).filter(Followers.user_no == user_id).first()
    print('followers: ', follow1)
    if(follow1):
        db.session.delete(follow1)
        db.session.commit()
    return redirect(url_for('profile_page',prof_user=user_id))


@app.route('/update_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    user_id = current_user.id
    post1 = Posts.query.get(post_id)
    print('Update: ', post1.post_title, request.method)
    if(post1):
        if request.method == 'GET':
            return render_template("update_post.html", post=post1)
        if request.method == 'POST':
            post_name = request.form["name"]
            desc = request.form["desc"]
            img_name = request.form["img_name"]
            current_timestamp = datetime.datetime.now()
            post1.post_title = post_name
            post1.description = desc
            post1.image_url = img_name
            post1.post_updated_ts = current_timestamp
            print('Updated ts: ', post1.post_updated_ts)
            db.session.commit()
            return redirect(url_for('profile_page',prof_user=user_id))
    return redirect(url_for('profile_page', prof_user=user_id))

@app.route('/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    user_id = current_user.id
    post1 = Posts.query.get(post_id)
    if(post1):
        db.session.delete(post1)
        db.session.commit()
    return redirect(url_for('profile_page',prof_user=user_id))


@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    user_id = current_user.id
    print('Like: ', user_id, post_id)
    post1 = Posts.query.get(post_id)
    print('current like: ', post1.likes)
    post1.likes += 1
    db.session.commit()
    return redirect(url_for('viewfeed'))


@app.route('/dislike/<int:post_id>')
@login_required
def dislike_post(post_id):
    user_id = current_user.id
    print('Dislike: ', user_id, post_id)
    post1 = Posts.query.get(post_id)
    print('current dislike: ', post1.dislikes)
    post1.dislikes += 1
    db.session.commit()
    return redirect(url_for('viewfeed'))


@app.route('/addcomment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def addcomment(post_id):
    comment_text = request.form['new_comment']
    user_name = current_user.username
    print('comment: ', user_name, post_id, comment_text)
    post1 = Posts.query.get(post_id)
    if(post1 is not None and comment_text > ''):
        new_comment = Comments(comment_text=comment_text, post_id=post_id, user_name=user_name)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('viewfeed'))


@app.route('/delete_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def delete_comment(comment_id):
    print('input: ', comment_id)
    comment = Comments.query.get(comment_id)
    print('delete comment: ', comment_id)
    if comment:
        print(comment.user_name, current_user.username)
        if(comment.user_name == current_user.username):
            print('deleting.......', comment.comment_text)
            db.session.delete(comment)
            db.session.commit()
    return redirect(url_for('viewfeed'))


@app.route('/export')
@login_required
def export_post():
    user_id = current_user.id
    conn = sqlite3.connect("blog.db")
    sql_query = "select * from posts where user_no = %d" % user_id
    df = pd.read_sql_query(sql_query, conn)

    for i in range(df.shape[0]):
        print(df.iloc[i,0])
        post_id = df.iloc[i,0]
        sql_query1 = "select comment_text, post_id, user_name from comments where post_id = %d" % post_id
        df1 = pd.read_sql_query(sql_query1, conn)
        for j in range(df1.shape[0]):
            col = 'comments'+str(j+1)
            df[col] = str(df1.iloc[j,0]) + ' - commented by: ' + str(df1.iloc[j,2])
    file_name = 'exports/posts_' + current_user.username + '.csv'
    print('file name: ',file_name)
    print('current dir', current_dir)
    exp_file = os.path.join(current_dir, file_name)
    df.to_csv(exp_file)
    return render_template("export_message.html", file_path=file_name, prof_user=user_id)


@app.route('/logout')
# @login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.debug = True
    app.run()
