# AWS Elastic Beanstalk looks for an "application" callable in application.py
from app import app as application

if __name__ == "__main__":
    application.run()
