def send_email():
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    gmail_user = "peterclaydon@peterclaydon.com"
    gmail_pwd = "Jackson3927"
    FROM = 'peterclaydon@peterclaydon.com'
    TO = ['peter.claydon@continuumbridge.com'] #must be a list
    SUBJECT = "Testing sending using gmail"
    '''
    TEXT = "Testing\r I hope that I will see some numbers in columns below \r \
            Time\t\tIn\t\tOut\r \
            10:41\t\t57\t\t102\r \
            11:14\t\t205.76\t\t91\r"
    '''
    text = "Plain text"
    #with open("table.html", 'r') as f:
    #  html = f.read() 
    html = "<html> </html>"
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    msg['To'] = TO
    msg.attach(part1)
    msg.attach(part2)
    # Prepare actual message
    #message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    #""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
    print "About to send mail"
    server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
    server.ehlo()
    server.starttls()
    server.login(gmail_user, gmail_pwd)
    #server.sendmail(FROM, TO, message)
    message = "Hello"
    server.sendmail(FROM, TO, msg.as_string())
    #server.quit()
    server.close()
    print 'successfully sent the mail'

if __name__ == '__main__':
    send_email()
