from blog_project import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    type = db.Column(db.String(20))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    liked = db.relationship('PostLike', foreign_keys='PostLike.user_id',
                            backref='user', lazy='dynamic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def like(self, post):
        if not self.has_liked(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike(self, post):
        if self.has_liked(post):
            PostLike.query.filter_by(user_id=self.id, post_id=post.id).delete()

    def has_liked(self, post):
        return PostLike.query.filter(PostLike.user_id == self.id,
                                     PostLike.post_id == post.id).count() > 0


class GoogleUser(User):
    occupation = db.Column(db.String(20), default='')
    __mapper_args__ = {
        'polymorphic_identity': 'google_user'
    }

    def __repr__(self):
        return f"GoogleUser('{self.username}', '{self.email}', '{self.occupation}')"


class FacebookUser(User):
    phone_number = db.Column(db.String(11), default='')
    __mapper_args__ = {
        'polymorphic_identity': 'facebook_user'
    }

    def __repr__(self):
        return f"FacebookUser('{self.username}', '{self.email}', '{self.phone_number}')"


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')

    def __repr__(self):
        return f"Post('{self.title}', '{self.content}')"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

