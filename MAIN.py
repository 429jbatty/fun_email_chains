import logic as logic
import datetime

sender = "429jbatty@gmail.com"
email_recipients = ["429jbatty@gmail.com", "schmidte96@gmail.com"]

jacob_email = ["429jbatty@gmail.com"]

if datetime.date.today().weekday() == 6:
    print("Sending Sunday text")
    chooser = logic.get_chooser()
    logic.send_sunday_email(chooser,email_recipients)

elif datetime.date.today().weekday() in [5,4]:
    print("Sending Reminder Text")
    logic.send_reminder_email(email_recipients)

else:
    logic.send_email(jacob_email,"AOTW Script Working","Script is working.")



