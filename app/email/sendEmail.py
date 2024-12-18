#!/usr/bin/python

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.email.emailConfig import emailConfig
from email.mime.base import MIMEBase
from email import encoders
import os


def sendEmailWithMultipleAttachments(sender, recipient, subject, message, file_locations):
    try:
        # SMTP server credentials
        username = 'farabix.com'
        password = 't29CBb3uRNFqoF4N'

        # Create a multipart message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        # Create a MIMEText object for the message
        message_body = MIMEText(message, 'plain')
        msg.attach(message_body)

        # Attach a file
        for file_location in file_locations:
            part = MIMEBase('application', "octet-stream")
            with open(file_location, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{file_location}"')
            msg.attach(part)

        # Send the email
        mailServer = smtplib.SMTP('mail.smtp2go.com', 2525)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(username, password)
        mailServer.sendmail(sender, recipient, msg.as_string())
        mailServer.close()

        return "Email sent successfully"

    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


def sendEmailInternal(sender, recipient, subject, message):
    try:
        # SMTP server credentials
        username = 'farabix.com'
        password = 't29CBb3uRNFqoF4N'

        # Create a multipart message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        # Create a MIMEText object for the message
        message_body = MIMEText(message, 'plain')
        msg.attach(message_body)

        # Send the email
        mailServer = smtplib.SMTP('mail.smtp2go.com', 2525)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(username, password)
        mailServer.sendmail(sender, recipient, msg.as_string())
        mailServer.close()

        return "Email sent successfully"

    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


def sendEmail(sender, recipient, email_type, url=None):

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
        if url:
            html_content = html_content.format(url=url)

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