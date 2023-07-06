#Copyright (c) Microsoft. All rights reserved.
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utilities.azure import keyvaultOperations
import utilities.config as config

def EmailNotification(subj,body,tolist,smtpServer='smtp-mail.outlook.com',smtpPort=587):
    
    (senderMail, senderPassword) = keyvaultOperations.getSecrets([config.mailusername,config.mailpassword])
    
    msg = MIMEMultipart()
    msg['From'] = senderMail
    msg['Subject'] = subj
    body = body
    msg.attach(MIMEText(body, 'plain'))
    # Log in to your email account
    username = senderMail
    password = senderPassword
    server = smtplib.SMTP(smtpServer, smtpPort)
    server.starttls()
    server.login(username, password)
    # Send the email to each client
    for client in tolist:
        msg['To'] = client
        server.sendmail(username, client, msg.as_string())
    # Close the SMTP server connection
    server.quit()