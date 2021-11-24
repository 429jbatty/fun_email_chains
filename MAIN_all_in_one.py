import datetime
import smtplib 


def send_text(
    recipients:list,
    body:str):
    
    recipients_addr = [num+"@email.uscc.net" for num in recipients]
    #recipients_addr = [num+"@gmail.com" for num in recipients]

    #Configure gmail login
    sender = "429jbatty@gmail.com"
    pas = "Boomer1!"

    smtp = "smtp.gmail.com" 
    port = 587
    server = smtplib.SMTP(smtp,port)
    server.starttls()
    server.login(sender,pas)

    #Send SMS
    server.sendmail(sender,recipients_addr,body)

    #Quit server
    server.quit()

    return print("Message Sent")

def send_email(
    recipients:list,
    subject:str,
    body:str):
    
    #Configure gmail login
    sender = "429jbatty@gmail.com"
    pas = "Boomer1!"

    #Set up server
    smtp = "smtp.gmail.com" 
    port = 587
    server = smtplib.SMTP(smtp,port)
    server.starttls()
    server.login(sender,pas)

    #Create message
    message = ("From: %s\r\n" % sender 
            + "To: %s\r\n" % sender
            + "CC: %s\r\n" % ",".join(recipients)
            + "Subject: %s\r\n" % subject
            + "\r\n" 
            + body)

    recipients_addr = [sender] + recipients

    #Send message
    server.sendmail(sender,recipients_addr,message)

    #Quit server
    server.quit()

    return print("Message Sent")

def get_chooser():
    choosers = ["Andrew","Sam","Jacob","Mom","Emily","Dad","Ashley"]
    week = datetime.date.today().isocalendar()[1]
    offset = 6

    chooser = choosers[(week%len(choosers)+ offset) % len(choosers)] 

    return chooser

def send_sunday_email(chooser,recipients):
    subject = "New AOTW from " + chooser +"!!!"
    
    body = (
        "Time for a new AOTW! It is "+chooser+"'s turn to choose an album. " +
        "Respond to this email chain with your score x/10 for the album and to engage in civil discussion with the other listeners."
        )

    send_email(recipients,subject,body)

    return print("Email Sent!")

def send_reminder_email(recipients):
    today = datetime.date.today()
    days_left =  6 - int(today.weekday())

    body = "Remember to listen to the AOTW! You have "+str(days_left)+" days left to listen."
    subject = "AOTW Reminder - "+str(days_left)+" Days Left to Listen"

    send_email(recipients,subject,body)
    return print("Email Sent!")


##### MAIN #####
sender = "429jbatty@gmail.com"

email_recipients = [
    "429jbatty@gmail.com", 
    "schmidte96@gmail.com",
    "ashleyebattenberg@gmail.com",
    "sbattenberg@wisc.edu",
    "andrewbatt33@gmail.com",
    "steve.battenberg@carlsonblack.com",
    "deb.battenberg@gmail.com"]

jacob_email = ["429jbatty@gmail.com"]

if datetime.date.today().weekday() == 6:
    print("Sending Sunday Email")
    chooser = get_chooser()
    send_sunday_email(chooser,email_recipients)

elif datetime.date.today().weekday() in [5,4]:
    print("Sending Reminder Email")
    send_reminder_email(email_recipients)

else:
    send_email(jacob_email,"AOTW Script Working","Script is working.")



