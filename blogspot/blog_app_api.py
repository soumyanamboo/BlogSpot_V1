from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index

from flask_cors import CORS

current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "blog.db")
CORS(app)
db = SQLAlchemy()
db.init_app(app)
api = Api(app)
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


user_parser = reqparse.RequestParser()
user_parser.add_argument("username")
user_parser.add_argument("email")
user_parser.add_argument("password")
user_parser.add_argument("repassword")

post_parser = reqparse.RequestParser()
post_parser.add_argument("post_title")
post_parser.add_argument("description")
post_parser.add_argument("likes")
post_parser.add_argument("dislikes")
post_parser.add_argument("post_user")
post_parser.add_argument("post_action")

feed_parser = reqparse.RequestParser()
feed_parser.add_argument("comment")


class UserAPI(Resource):
    def get(self, user_id):
        try:
            u1 = User.query.get(user_id)
            if u1 is None:
                return 'User not found', 404
            else:
                followers_list = Followers.query.filter(Followers.following_user == user_id).all()
                following_list = Followers.query.filter(Followers.user_no == user_id).all()
                data = {
                    "user_id": u1.id,
                    "user_name": u1.username,
                    "email": u1.email,
                    "followers_count": len(followers_list),
                    "following_count": len(following_list)
                }
                print('User GET - ', data)
                return data, 200
        except:
            return 'Internal Server Error', 500

    def put(self, user_id):
        args = user_parser.parse_args()
        email = args.get("email", None)
        password = args.get("password", None)
        print('put: ', email, password)

        if email is None:
            data = {'error_code': "USER002", 'error_message': "Email is required."}
            return data, 400
        elif ('@' not in email) or ('.' not in email):
            data = {'error_code': "USER003", 'error_message': "Invalid Email."}
            return data, 400
        elif len(password) < 8:
            data = {'error_code': "USER004", 'error_message': "Password should be minimum 8 characters."}
            return data, 400
        else:
            try:
                u1 = User.query.get(user_id)
                if u1 is None:
                    return 'User not found', 404
                else:
                    if (check_password_hash(u1.password, password)):
                        mail = db.session.query(User).filter(User.email == email).first()
                        if (mail is not None):
                            data = {'error_code': "USER006",
                                    'error_message': "Email already exists!"}
                            return data, 400
                        u1.email = email
                        db.session.commit()
                        data = {
                            "User_id": u1.id,
                            "User_name": u1.username,
                            "Email": u1.email,
                        }
                        return data, 200
                    else:
                        data = {'error_code': "USER007", 'error_message': "Wrong Password !!!"}
                        return data, 400
            except:
                return 'Internal Server Error', 500

    def delete(self, user_id):
        print('delete user')
        try:
            u1 = User.query.get(user_id)
            if u1 is None:
                return 'User not found', 404
            else:
                c1 = Comments.query.filter(Comments.user_name == u1.username).all()
                print('comments from delete: ', c1)
                for c in c1:
                    db.session.delete(c)
                followers_list = db.session.query(Followers).filter(Followers.user_no == user_id).all()
                if len(followers_list) > 0:
                    for f1 in followers_list:
                        db.session.delete(f1)
                followers_list = db.session.query(Followers).filter(Followers.following_user == user_id).all()
                if len(followers_list) > 0:
                    for f1 in followers_list:
                        db.session.delete(f1)
                db.session.delete(u1)
                db.session.commit()
                return "Successfully Deleted", 200
        except:
            return 'Internal Server Error', 500

    def post(self):
        try:
            args = user_parser.parse_args()
            uname = args.get("username", None)
            email = args.get("email", None)
            password = args.get("password", None)
            repassword = args.get("repassword", None)
            print('POST: ', uname, email, password)
            if uname is None:
                data = {'error_code': "USER001", 'error_message': "User Name is required."}
                return data, 400
            elif email is None:
                data = {'error_code': "USER002", 'error_message': "Email is required."}
                return data, 400
            elif not ('@' in email or '.' in email):
                data = {'error_code': "USER003", 'error_message': "Invalid Email."}
                return data, 400
            elif len(password) < 8:
                data = {'error_code': "USER004", 'error_message': "Password should be minimum 8 characters."}
                return data, 400
            elif password != repassword:
                data = {'error_code': "USER006", 'error_message': "Passwords are not matching."}
                return data, 400
            else:
                pwd: str = generate_password_hash(password, method='md5')
                u1 = db.session.query(User).filter(User.username == uname).first()
                u2 = db.session.query(User).filter(User.email == email).first()
                if u1 is None and u2 is None:
                    new_user = User(username=uname, password=pwd, email=email, profile_image=None)
                    db.session.add(new_user)
                    db.session.commit()
                    data = {
                        "User_id": new_user.id,
                        "User_name": new_user.username,
                        "Email": new_user.email,
                    }
                    return data, 201
                else:
                    if not (u1 is None):
                        return 'User name already exist', 409
                    if not (u2 is None):
                        return 'Email already exist', 409
        except:
            print('Exception')
            return 'Internal Server Error', 500


class PostAPI(Resource):
    def get(self, post_id):
        try:
            p1 = Posts.query.filter(Posts.post_id == post_id).first()
            print('GET: ', post_id, p1)
            if p1 is None:
                return 'Post Not Found', 404
            else:
                comment_list = []
                comments = Comments.query.filter(Comments.post_id == p1.post_id).all()
                for c in comments:
                    comment_list.append({
                        "comment": c.comment_text,
                        "user": c.user_name
                    })
                data = {"post_title": p1.post_title,
                        "description": p1.description,
                        "creted_time": str(p1.post_created_ts),
                        "likes": p1.likes,
                        "dislikes": p1.dislikes,
                        "post_user": p1.user_no,
                        "updated_time": str(p1.post_updated_ts),
                        "comments": comment_list
                        }
                print(data)
                return data, 200
        except:
            return 'Internal Server Error', 500

    def put(self, post_id):
        args = post_parser.parse_args()
        title = args.get("post_title", None)
        desc = args.get("description", None)
        post_user = args.get("post_user", None)
        post_action = args.get("post_action", None)
        if title is None:
            data = {'error_code': "POST001", 'error_message': "Post Title is required."}
            return data, 400
        elif post_user is None:
            data = {'error_code': "POST002", 'error_message': "User id is required."}
            return data, 400
        else:
            try:
                print('POST PUT: ', post_id, post_user)
                # db.session.query(Posts).filter(Posts.user_no == user_id)
                p1 = Posts.query.filter(Posts.post_id == post_id).first()
                if p1 is None:
                    return 'Post not found', 404
                else:
                    if (int(p1.user_no) != int(post_user)):
                        print('not equal')
                        data = {'error_code': "POST003", 'error_message': "Post not created by user"}
                        return data, 400
                    current_timestamp = datetime.datetime.now()
                    p1.post_title = title
                    p1.description = desc
                    p1.post_updated_ts = current_timestamp
                    p1.post_user = post_user
                    if (post_action == 'like'):
                        p1.likes += 1
                    elif (post_action == 'dislike'):
                        p1.dislikes += 1
                    db.session.commit()
                    data = {"post_title": p1.post_title,
                            "description": p1.description,
                            "likes": p1.likes,
                            "dislikes": p1.dislikes,
                            "updated_ts": str(p1.post_updated_ts)
                            }
                    print(data)
                    return data, 200
            except:
                return 'Internal Server Error', 500

    def delete(self, post_id):
        print('delete post')
        try:
            p1 = Posts.query.get(post_id)
            if p1 is None:
                return 'Post not found', 404
            else:
                db.session.delete(p1)
                db.session.commit()
                return "Successfully Deleted", 200
        except:
            return 'Internal Server Error', 500

    def post(self):
        try:
            current_timestamp = datetime.datetime.now()
            args = post_parser.parse_args()
            title = args.get("post_title", None)
            desc = args.get("description", None)
            post_user = args.get("post_user", None)

            if title is None:
                data = {'error_code': "POST001", 'error_message': "Post Title is required."}
                return data, 400
            elif post_user is None:
                data = {'error_code': "POST002", 'error_message': "User id is required."}
                return data, 400
            else:
                p1 = db.session.query(Posts).filter(Posts.post_title == title).first()
                print(p1)
                if p1 is None:
                    new_post = Posts(post_title=title, description=desc, likes=0, dislikes=0,
                                     post_created_ts=current_timestamp, post_updated_ts=current_timestamp,
                                     user_no=post_user, image_url=None)
                    print("test1")
                    db.session.add(new_post)
                    db.session.commit()
                    print(new_post.post_title)
                    data = {"Post_id": new_post.post_id,
                            "post_title": new_post.post_title,
                            "description": new_post.description,
                            "post_user": new_post.user_no,
                            "post_created_time": str(new_post.post_created_ts)
                            }
                    return data, 201
                else:
                    return 'Post title already exist', 409
        except:
            return 'Internal Server Error', 500


class FeedAPI(Resource):
    def get(self, user_id):
        try:
            u1 = User.query.get(user_id)
            if u1 is None:
                return 'User Not Found', 404
            else:
                feed_data = []
                following_list = Followers.query.filter(Followers.user_no == user_id).all()
                if (len(following_list) == 0):
                    data = {'error_code': "FEED001", 'error_message': "User Not following anyone."}
                    return data, 400
                else:
                    for item in following_list:
                        list1 = Posts.query.filter(Posts.user_no == item.following_user).order_by(
                            Posts.post_updated_ts.desc()).all()
                        for post in list1:
                            data = {"post_id": post.post_id,
                                    "post_title": post.post_title,
                                    "description": post.description,
                                    "creted time": str(post.post_created_ts),
                                    "likes": post.likes,
                                    "dislikes": post.dislikes,
                                    "post_user": post.user_no,
                                    "updated time": str(post.post_updated_ts)
                                    }
                            feed_data.append(data)
                    print(feed_data)
                    return feed_data, 200
        except:
            return 'Internal Server Error', 500


class CommentsAPI(Resource):
    def get(self, post_id):
        print('GET comments ', post_id)
        try:
            cmnt = Comments.query.filter(Comments.post_id == post_id).all()
            if cmnt is None:
                return 'No Comments Found for the post', 404
            else:
                comment_list = []
                for c in cmnt:
                    comment_list.append({
                        "comment_id": c.comment_id,
                        "comment": c.comment_text,
                        "user": c.user_name
                    })
            data = {"post_id": post_id,
                    "comments": comment_list
                    }
            return data, 200
        except:
            return 'Internal Server Error', 500

    def post(self, user_id, post_id):
        args = feed_parser.parse_args()
        comment = args.get("comment", None)
        print('POST comment:', comment)
        try:
            u1 = User.query.get(user_id)
            p = Posts.query.get(post_id)
            if u1 is None:
                return 'User Not Found', 404
            if p is not None:
                post_title = p.post_title
                desc = p.description
                likes = p.likes
                dislikes = p.dislikes
                post_user = p.user_no
                updated_ts = p.post_updated_ts

                new_comment = Comments(comment_text=comment, post_id=post_id, user_name=u1.username)
                db.session.add(new_comment)
                db.session.commit()
                print('comment added succesfully', u1.username)
                comment_list = []
                comments = Comments.query.filter(Comments.post_id == post_id).all()
                for c in comments:
                    comment_list.append({
                        "comment": c.comment_text,
                        "user": c.user_name
                    })
                    print(c.user_name)
                data = {"post_title": post_title,
                        "description": desc,
                        "likes": likes,
                        "dislikes": dislikes,
                        "post_user": post_user,
                        "updated time": str(updated_ts),
                        "comments": comment_list
                        }
                print(data)
                return data, 200
            else:
                data = {'error_code': "FEED002", 'error_message': "Wrong post_id."}
                return data, 400
        except:
            return 'Internal Server Error', 500


class TestAPI(Resource):
    def delete(self, comment_id):
        print('delete of comment', comment_id)
        try:
            c = Comments.query.get(comment_id)
            if c is None:
                return 'Comment not found', 404
            else:
                db.session.delete(c)
                db.session.commit()
                return "Successfully Deleted", 200
        except:
            return 'Internal Server Error', 500


api.add_resource(UserAPI, "/api/user", "/api/user/<int:user_id>")
api.add_resource(PostAPI, "/api/post", "/api/post/<int:post_id>")
api.add_resource(FeedAPI, "/api/feeds/<int:user_id>")
api.add_resource(CommentsAPI, "/api/comments/<int:post_id>", "/api/comments/<int:user_id>/<int:post_id>")
api.add_resource(TestAPI, "/api/comment/<int:comment_id>")

if __name__ == '__main__':
    app.debug = True
    app.run()
