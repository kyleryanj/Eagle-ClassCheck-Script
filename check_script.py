#BC Class Checker script
#Python version 2.7
#April 14th, 2015

import smtplib
import os
from time import sleep

from py3270 import Emulator
import MySQLdb
import threading
import smtplib
from email.mime.text import MIMEText
from twilio.rest import TwilioRestClient 


def check_script():
	db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
	cur = db.cursor() #placed here so that cur is initialized in case of KeyboardError
	em = Emulator()
	em.connect("bcvmcms.bc.edu")
	em.wait_for_field()
	em.fill_field(7, 46, uis_username, 9)
	em.fill_field(9, 46, uis_password, 15)
	em.send_enter()
	# em.fill_field(6, 44, '7', 4) #This is commented out for when BC changes the register page
	# em.send_enter()
	# em.fill_field(17, 34, '2', 1)
	# em.send_enter()
	em.fill_field(16, 22, 'c', 1)
	em.send_enter()
	cur.execute("select * from checker_class")
	for row in cur.fetchall():
		try:
		# print(row[1][:8])
		# print(row[1][8:])
			em.fill_field(3, 24, "", 8)
			em.send_enter()
			em.fill_field(3, 24, row[1][:8], 8)
			em.send_enter()
			sleep(.09)
			if not em.string_found(8, 19, "No Courses"):
				class_found = False
				i = 0
				page_turn = (int(row[1][8:]) - 1) / 16
				while page_turn != 0:
						em.send_enter()
						page_turn = page_turn - 1
				while class_found == False:
					if em.string_found(8+i, 15, row[1][8:]):
						if em.string_found(8+i, 68, "*CLOSED"):
							print row[1], " is closed"
							class_found = True
							break
						elif em.string_found(8+i, 68, "*CANCEL"):
							print row[1], " is cancelled"
							class_found = True
							break
						else:
							print row[1], " is open"
							cur.execute("select * from cc.checker_class_students c, cc.checker_student s where class_id = " + str(row[0]) + " and student_id = s.id")
							notify_thread=threading.Thread(target=notify_students, args=(cur.fetchall(), row))
							notify_thread.start()
							cur.execute("delete from cc.checker_class_students where class_id = " + str(row[0]))
							cur.execute("delete from cc.checker_class where id = " +str(row[0]))
							class_found = True
							break
					i+=1
			else:
				print("class not found")
		except Exception as e:
			print(e)
			continue
	#closing time
	cur.close()
	db.commit()
	em.fill_field(3, 24, "QUIT", 8)
	em.send_enter()
	em.fill_field(16, 22, "l", 1)
	em.send_enter()
	em.terminate()
	sleep(300)

def notify_students(students, class_code):
	gmail_user = email_user
	gmail_pwd = email_password
	smtpserver = smtplib.SMTP(email_smtp, email_portnum)
	smtpserver.ehlo()
	smtpserver.starttls()
	smtpserver.ehlo
	smtpserver.login(gmail_user, gmail_pwd)

	for student in students:
		if student[4] != 'none': #use phone number
			client = TwilioRestClient(twilio_account_sid, twilio_auth_token) 
			client.messages.create(to=student[4], from_="+16176006026", body=str(class_code[1]) + " is now open! Go register! If you didn't get in, you'll have to go to eagleclasscheck.com and re-track the class.")

		else:

			msg = MIMEText(str(class_code[1]) + " is now open! Go register! If you didn't get in, you'll have to go to eagleclasscheck.com and re-track the class.")
			msg['Subject'] = "A class is open!"
			msg['From'] = "ryanwn@bc.edu"
			msg['To'] = str(student[5])
			smtpserver.sendmail(gmail_user, [str(student[5])], msg.as_string())

	smtpserver.close()