from fastapi import FastAPI, Request, BackgroundTasks
from celery import Celery
import smtplib
from email.mime.text import MIMEText
import logging
from datetime import datetime
from celery.exceptions import SoftTimeLimitExceeded

# Initialize Celery without using Click-based CLI options
app_c = Celery('main', broker='amqp://guest:guest@localhost:5672//', backend='rpc://')

# Register task
@app_c.task(name='tasks.send_email_task')  # Ensure the task name matches the import path
def send_email_task(email):
    try:
        # email parameters
        msg = MIMEText(f" Testing my Messaging System. \n Have a great day!")
        msg['Subject'] = 'Hi there'
        msg['From'] = 'xxxxxxxx'  # Update with your email
        msg['To'] = email

        # SMTP server configuration
        smtp_server = 'xxxxxxx'
        smtp_port = 587
        smtp_user = 'xxxxxxx'  # Update with your email
        smtp_password = 'xxxxxx'  # Update with your app-specific password

        # Sending the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, email, msg.as_string())
        return "Email sent successfully"
    except SoftTimeLimitExceeded as e:
        # Handle soft time limit exceeded (if configured)
        return f"Task timeout: {str(e)}"
    except Exception as e:
        # Handle any other exceptions
        return f"Task failed: {str(e)}"

# Setting up logging
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

#function to create log of current time in /var/log/messaging_system
def log_time():
    logging.info(f"Current time: {datetime.now()}")

# Initialize FastAPI
app = FastAPI()

@app.get("/")
async def root(request: Request, background_tasks: BackgroundTasks):
    sendmail = request.query_params.get("sendmail") #get sendmail parameter
    talktome = request.query_params.get("talktome") #get talktome parameter

    if sendmail: #if there is a send mail parameter create email queue
        try: 
            result = send_email_task.delay(sendmail)#Create email queue function if sendmail parameter has an argument
            return {"message": f"Email queued with task id: {result.id} \n Check the Celery logs"}
        except Exception as e:
            logging.error(f"Error queueing email task: {str(e)}")
            return {"message": "Failed to queue email task"}

    if talktome: #if there is a talk to me parameter
        background_tasks.add_task(log_time) #Call log function if talktone parameter has an argument
        return {"message": "The current Time is logged successfully. \n Navigate to /var/log/messaging_system.log to view the logs"}

    # if talktome and sendmail parameters are not passed with the url, specify a query parameter
    return {"message": "Specify a query parameter in the url: Example(url/?sendmail) or (url/?talktome)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
