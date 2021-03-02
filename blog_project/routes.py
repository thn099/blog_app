from flask import jsonify, request
from blog_project import app, db, bcrypt
from blog_project.models import User, GoogleUser, FacebookUser, Post
from flask_login import login_user, logout_user, current_user, login_required


@app.route("/")
@app.route("/home")
def home():
    """ Return all posts of all users """
    posts = Post.query.all()
    post_dict = {}
    for post in posts:
        post_dict[post.id] = post.as_dict()
    return jsonify(post_dict), 200


@app.route("/posts")
@login_required
def posts():
    """ Return all posts of current user """
    if current_user.is_authenticated:
        posts = current_user.posts
        post_dict = {}
        for post in posts:
            post_dict[post.id] = post.as_dict()
        return jsonify(post_dict), 200
    else:
        return jsonify(), 404


@app.route("/posts/<int:post_id>")
def post(post_id):
    """ Return content and other info of post_id """
    post = Post.query.filter_by(id=post_id).first()
    count = post.likes.count()
    return jsonify(title=post.title,
                   author=post.author.username,
                   number_of_likes=count,
                   content=post.content)


@app.route("/posts/<int:post_id>", methods=['DELETE'])
def delete_post(post_id):
    """ Allow user to delete post """
    post = Post.query.filter_by(id=post_id).first()
    if post.author != current_user:
        return jsonify({'message': 'You are not authorized to delete this post'}), 403
    if post is None:
        return jsonify({'message': 'Post not found'}), 404
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post has been deleted'}), 200


@app.route("/signup/google",  methods=['GET', 'POST'])
def sign_up_with_google():
    """ Allow user to create an account using Google account.
    """
    if current_user.is_authenticated:
        return jsonify({'message': 'Must log out before creating a new account'}), 403

    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    # Assume Google email is validated

    if username is None or email is None or password is None:
        return jsonify({'message': 'Missing argument'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user is not None:
        # if user already sign up using Facebook
        if existing_user.type == 'facebook_user':
            return jsonify({'message': 'Redirect user to verify Facebook account'}), 303
        else:
            return jsonify({'message': 'Redirect user to log in page'}), 303

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    if 'occupation' in request.json:
        occupation = request.json.get('occupation')
        user = GoogleUser(username=username, email=email,
                          password=hashed_password, occupation=occupation)
        db.session.add(user)
        db.session.commit()
        return {'message': 'Account created'}, 201
    else:
        user = GoogleUser(username=username, email=email,
                          password=hashed_password)
        db.session.add(user)
        db.session.commit()

        return {'message': 'Redirect user to choose occupation'}, 201


@app.route("/signup/facebook", methods=['GET', 'POST'])
def sign_up_with_facebook():
    """ Allow user to create an account using Facebook account.
    """
    if current_user.is_authenticated:
        return jsonify({'message': 'Must log out before creating a new account'}), 400

    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    # Assume Facebook email is validated

    if username is None or email is None or password is None:
        return jsonify({'message': 'Missing argument'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user is not None:
        # if user already sign up using Google
        if existing_user.type == 'google_user':
            return jsonify({'message': 'Redirect user to verify Google account'}), 303
        else:
            return jsonify({'message': 'Redirect user to log in page'}), 303

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'message': 'Username taken'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    if 'phone_number' in request.json:
        phone_number = request.json.get('occupation')
        user = FacebookUser(username=username, email=email,
                            password=hashed_password,
                            phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        return {'message': 'Account created'}, 201
    else:
        user = FacebookUser(username=username, email=email,
                            password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return {'message': 'Redirect user to fill phone number'}, 201


@app.route("/login", methods=['GET', 'POST'])
def login():
    """ Allow user to log in using website username and password """
    if current_user.is_authenticated:
        return jsonify({'message': 'You must log out first'}), 403

    email = request.json.get('email')
    password = request.json.get('password')

    if email and password:
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return jsonify({'message': 'Logged in'}), 200
        else:
            return jsonify({'message': 'One of the entered field is incorrect'}), 401
    else:
        return jsonify({'message': 'Missing argument'}), 400


@app.route("/logout")
@login_required
def logout():
    """ Log current user out """
    logout_user()
    return jsonify({'message': 'Logged out'}), 200


@app.route("/account")
@login_required
def account():
    """ Return information of current user """
    return jsonify(username=current_user.username,
                   email=current_user.email,
                   id=current_user.id,
                   account_type=current_user.type)


@app.route("/posts", methods=['POST'])
@login_required
def new_post():
    """ Allow user to create new post with title and content """
    title = request.json.get('title')
    content = request.json.get('content')

    post = Post(title=title, content=content, author=current_user)

    db.session.add(post)
    db.session.commit()

    return jsonify({'message': 'New post created'}), 201


@app.route('/posts/<int:post_id>/like', methods=['GET', 'DELETE'])
@login_required
def like_or_unlike(post_id, action):
    """ Allow user to like/unlike a post"""
    post = Post.query.filter_by(id=post_id).first()
    if request.method == 'POST':
        current_user.like(post)
        db.session.commit()
        return jsonify({'message': 'Liked'}), 200
    else:
        current_user.unlike(post)
        db.session.commit()
        return jsonify({'message': 'Unliked'}), 200


@app.route('/posts/<int:post_id>/<action>')
@login_required
def action(post_id, action):
    """ Allow user to get some statistics of a post
    """
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return jsonify({'message': 'Can\'t find this post'}), 404
    if action == 'number_of_likes':
        count = post.likes.count()
        return jsonify(post_id=post.id, number_of_likes=count), 200
    if action == 'likes':  # get names of users who liked this post
        user_dict = {}
        for like in post.likes:
            user_id = like.user_id
            user = User.query.filter_by(id=user_id).first()
            user_dict[user_id] = user.username
        return jsonify(user_dict), 200
    else:
        return jsonify({'message': 'Action not supported'}), 400


@app.route('/account', methods=['PUT'])
@login_required
def update_profile():
    """ Update phone number for Facebook user or occupation for Google user """
    phone_number = request.json.get('phone_number')
    occupation = request.json.get('occupation')

    if phone_number:
        if current_user.type == 'facebook_user':
            setattr(current_user, 'phone_number', phone_number)
            db.session.commit()
            return jsonify({'message': 'Phone number updated'}), 200
        else:
            return jsonify({'message': 'Can only update phone number of Facebook user'}), 400

    if occupation:
        if current_user.type == 'google_user':
            setattr(current_user, 'occupation', occupation)
            db.session.commit()
            return jsonify({'message': 'Occupation updated'}), 200
        else:
            return jsonify(
                {'message': 'Can only update occupation of Google user'}), 400

    return jsonify({'message': 'Invalid argument'}), 400
