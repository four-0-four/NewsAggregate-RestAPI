#!/usr/bin/python

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.email.emailConfig import emailConfig
import os


def sendEmail(sender, recipient, email_type, reset_url=None):

    # SMTP server credentials
    username = 'farabix.com'
    password = 't29CBb3uRNFqoF4N'

    email_content = emailConfig[email_type]

    # Create a multipart message
    msg = MIMEMultipart('mixed')
    msg['Subject'] = email_content['subject']
    msg['From'] = sender
    msg['To'] = recipient

    with open(email_content['html_file'], 'r') as f:
        html_content = f.read()
        if reset_url:
            html_content = html_content.format(reset_url=reset_url)

    html_message = MIMEText(html_content, 'html')
    msg.attach(html_message)

    # Send the email
    mailServer = smtplib.SMTP('mail.smtp2go.com', 2525)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(username, password)
    mailServer.sendmail(sender, recipient, msg.as_string())
    mailServer.close()