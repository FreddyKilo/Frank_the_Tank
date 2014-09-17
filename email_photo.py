#!/usr/bin/env python

'''running as bash command i.e. "email_photo.py image.jpg someone@gmail.com&"
   will send email in background'''

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

def SendMail(ImgFileName, To):

    From = "your email here"
    Password = "your password here"
    Subject = "subject goes here"
    Body = "text body goes here"
    Attachment = "image.jpg"

    img_data = open(ImgFileName, 'rb').read()
    msg = MIMEMultipart()
    msg['Subject'] = Subject
    msg['From'] = From
    msg['To'] = To

    text = MIMEText(Body)
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename(ImgFileName))
    msg.attach(image)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(From, Password)
    s.sendmail(From, To, msg.as_string())
    s.quit()

SendMail(sys.argv[1], sys.argv[2])