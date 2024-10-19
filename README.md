QnA App

## Functionality

Application provides different functionality to 3 types of user's:
user, admin, expert

All three types of users can register, login, logout, and see a list of answered questions.

- Users can ask a question and can select an expert
- Admin users can update users' setup by promoting a registered user to an expert
- Expert users can see a list of questions to be answered, and can answer a question

## Specification

HTML, CSS, Flask, Python, PostgreSQL

Deployed on Heroku: [QnA app](https://qnda-app-720ed0376dc9.herokuapp.com/)

# TODO:

Fix issue between local (route 5000) and production (Heroku) environments

- Issue statements:

* basic user can log in but CANNOT open the links to answered questions in production (Heroku) environment
* basic user can log in and CAN open the links to answered questions in local (5000) environment
* admin user can log in but CANNOT open the links to USERS SETUP in production (Heroku) environment
* admin user can log in and CAN open the links to USERS SETUP in local (5000) environment
