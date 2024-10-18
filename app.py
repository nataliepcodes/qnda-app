from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # generate random string of 24 characters

# Close the curser and connection everytime a request ends
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()

    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()

# Function for user session
def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        db.execute('SELECT id, name, password, expert, admin FROM users WHERE name = %s', (user, ))
        user_result = db.fetchone()
    
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    
    db = get_db()
    db.execute('''SELECT
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
    question_result = db.fetchall()

    return render_template('home.html', user=user, answered_questions=question_result) 


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    
    if request.method == 'POST':
        db = get_db()

        # Check if user exists
        db.execute('SELECT id FROM users WHERE name = %s', (request.form['name'], ))
        existing_user_result = db.fetchone()

        if existing_user_result:
            return render_template('register.html', user=user, error='User already exists! Try to Login.') 

        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.execute('INSERT INTO users (name, password, expert, admin) VALUES (%s, %s, %s, %s)', (request.form['name'], hashed_password, '0', '0', ))
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
        db.execute('SELECT id, name, password FROM users WHERE name = %s', (name, ))
        user_result = db.fetchone()

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
        db.execute('INSERT INTO questions (question_text, asked_by_id, expert_id) VALUES (%s, %s, %s)', (request.form['question'], user['id'], request.form['expert'], ))
        return redirect(url_for('index'))
    
    # Querying db for a list of experts to be listed in the form selection drop down
    db.execute('SELECT id, name FROM users WHERE expert = True')
    expert_results = db.fetchall()

    return render_template('ask.html', user=user, experts=expert_results) 


@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    db.execute('''SELECT 
                      questions.id, 
                      questions.question_text, 
                      questions.answer_text, 
                      askers.name as asker_name, 
                      experts.name as expert_name 
                  FROM questions 
                  JOIN users as askers ON askers.id = questions.asked_by_id 
                  JOIN users as experts ON experts.id = questions.expert_id 
                  WHERE questions.id = %s''', (question_id, ))
    question_result = db.fetchone()

    return render_template('question.html', user=user, question=question_result) 


@app.route('/answer/<question_id>', methods=['GET', 'POST']) 
def answer(question_id):
    user = get_current_user()
    
    if not user:
        return redirect(url_for('login'))
    
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()
    
    if request.method == 'POST':
        db.execute('UPDATE questions SET answer_text = %s WHERE id = %s', (request.form['answer'], question_id, ))
        return redirect(url_for('unanswered'))
    
    db.execute('SELECT id, question_text FROM questions WHERE id = %s', (question_id, ))
    question_result = db.fetchone()

    return render_template('answer.html', user=user, question=question_result)  


@app.route('/unanswered') 
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()
    db.execute('''SELECT questions.id, questions.question_text, users.name 
                                  FROM questions 
                                  JOIN users on users.id = questions.asked_by_id 
                                  WHERE questions.answer_text is null and questions.expert_id = %s''', (user['id'], ))
    questions_results = db.fetchall()

    return render_template('unanswered.html', user=user, questions=questions_results)


@app.route('/users') 
def users():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if not user['admin']:
        return redirect(url_for('index'))

    # Query all the users in the db and pass the list to the users template
    db = get_db()
    db.execute('SELECT id, name, expert, admin FROM users')
    users_results = db.fetchall()

    return render_template('users.html', user=user, users=users_results)


@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if not user['admin']:
        return redirect(url_for('index'))
    
    db = get_db()

    db.execute('SELECT id, expert FROM users WHERE id = %s', (user_id, ))
    user_result = db.fetchone()

    if user_result['expert']:
        db.execute('UPDATE users SET expert = False WHERE id = %s', (user_id, ))
    else:
        db.execute('UPDATE users SET expert = True WHERE id = %s', (user_id, ))

    return redirect(url_for('users'))


@app.route('/logout')
def logout():
    # Remove user from the Session
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
