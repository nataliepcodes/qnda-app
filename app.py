from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # generate random string of 24 characters

# Close the db everytime a request ends
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# Function for user session
def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur = db.execute('SELECT id, name, password, expert, admin FROM users WHERE name = ?', [user])
        user_result = user_cur.fetchone()
    
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    
    db = get_db()
    questions_cur = db.execute('''SELECT
                                      questions.id as question_id, 
                                      questions.question_text, 
                                      askers.name as asker_name, 
                                      experts.name as expert_name 
                                  FROM questions 
                                  JOIN users as askers 
                                  ON askers.id = questions.asked_by_id 
                                  JOIN users as experts 
                                  ON experts.id = questions.expert_id 
                                  WHERE questions.answer_text is not null''')
    question_result = questions_cur.fetchall()

    return render_template('home.html', user=user, answered_questions=question_result) 


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    
    if request.method == 'POST':
        db = get_db()

        # Check if user exists
        existing_user_cur = db.execute('SELECT id FROM users WHERE name = ?', [request.form['name']])
        existing_user_result = existing_user_cur.fetchone()

        if existing_user_result:
            return render_template('register.html', user=user, error='User already exists! Try to Login.') 

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('INSERT INTO users (name, password, expert, admin) VALUES (?, ?, ?, ?)', [request.form['name'], hashed_password, '0', '0'])
        db.commit()
        #to test: return '<h1>Name: {}, Password: {}</h1>'.format(request.form['name'], request.form['password'])
        session['user'] = request.form['name']

        return redirect(url_for('index'))

    return render_template('register.html', user=user) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    
    if request.method == 'POST':
        db =get_db()
        name = request.form['name']
        password = request.form['password']
        user_cur = db.execute('SELECT id, name, password FROM users WHERE name = ?', [name])
        user_result = user_cur.fetchone()

        # Check if the name exists
        if user_result:
            # Check that the password stored in the db and the password entered into the form match
            if check_password_hash(user_result['password'], password):
                # Create a session with name from database
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                return render_template('login.html', user=user, error='The password is incorrect.') 
        else:
            return render_template('login.html', user=user, error='The username is incorrect.') 
    
    return render_template('login.html', user=user) 


@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    db = get_db()

    # Taking form input and inserting into the questions.db
    if request.method == 'POST':
        db.execute('INSERT INTO questions (question_text, asked_by_id, expert_id) VALUES (?, ?, ?)', [request.form['question'], user['id'], request.form['expert']])
        db.commit()
        return redirect(url_for('index'))
    
    # Querying db for a list of experts to be listed in the form selection drop down
    expert_cur = db.execute('SELECT id, name FROM users WHERE expert = 1')
    expert_results = expert_cur.fetchall()

    return render_template('ask.html', user=user, experts=expert_results) 


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    question_cur = db.execute('''SELECT 
                                     questions.id, 
                                     questions.question_text, 
                                     questions.answer_text, 
                                     askers.name as asker_name, 
                                     experts.name as expert_name 
                                 FROM questions 
                                 JOIN users as askers ON askers.id = questions.asked_by_id 
                                 JOIN users as experts ON experts.id = questions.expert_id 
                                 WHERE questions.id = ?''', [question_id])
    question_result = question_cur.fetchone()

    return render_template('question.html', user=user, question=question_result) 


@app.route('/answer/<question_id>', methods=['GET', 'POST']) 
def answer(question_id):
    user = get_current_user()
    
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()
    
    if request.method == 'POST':
        db.execute('UPDATE questions SET answer_text = ? WHERE id = ?', [request.form['answer'], question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    
    question_cur = db.execute('SELECT id, question_text FROM questions WHERE id = ?', [question_id])
    question_result = question_cur.fetchone()

    return render_template('answer.html', user=user, question=question_result)  


@app.route('/unanswered') 
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()
    questions_cur = db.execute('''SELECT questions.id, questions.question_text, users.name 
                                  FROM questions 
                                  JOIN users on users.id = questions.asked_by_id 
                                  WHERE questions.answer_text is null and questions.expert_id = ?''', [user['id']])
    questions_results = questions_cur.fetchall()

    return render_template('unanswered.html', user=user, questions=questions_results)


@app.route('/users') 
def users():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        return redirect(url_for('index'))

    # Query all the users in the db and pass the list to the users template
    db = get_db()
    users_cur = db.execute('SELECT id, name, expert, admin FROM users')
    users_results = users_cur.fetchall()

    return render_template('users.html', user=user, users=users_results)


@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()

    user_cur = db.execute('SELECT id, expert FROM users WHERE id = ?', [user_id])
    user_result = user_cur.fetchone()

    if user_result['expert'] == 1:
        db.execute('UPDATE users SET expert = 0 WHERE id = ?', [user_id])
        db.commit()
    else:
        db.execute('UPDATE users SET expert = 1 WHERE id = ?', [user_id])
        db.commit()

    return redirect(url_for('users'))


@app.route('/logout')
def logout():
    # Remove user from the Session
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)