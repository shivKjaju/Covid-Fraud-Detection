import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import glob
import os

# Get the data from CDC api endpoint and clean it
response = requests.get('https://data.cdc.gov/resource/r8kw-7aab.json')
data = response.json()
data = pd.DataFrame.from_records(data)
data = data[data['covid_deaths'].notna()]
sample_data = data[['start_week', 'covid_deaths']]
result_data = sample_data.groupby('start_week')

# Process the data and count the number of First digits (Benford's law)
result_data_agg = pd.DataFrame(columns=['number', 'count'])
count = 0
for i in range(len(sample_data)):
    number = int(str(sample_data.iloc[i]['covid_deaths'])[0])
    if(number == 0):
        continue
    count += 1
    if(len(result_data_agg[result_data_agg['number'] == number]) > 0):
        result_index = result_data_agg[result_data_agg['number'] == number].index.values.astype(int)[
            0]
        result_data_agg.iloc[result_index]['count'] = result_data_agg.iloc[result_index]['count']+1

    else:
        result_data_agg = result_data_agg.append(
            {'number': number, 'count': 1}, ignore_index=True)

# Convert the count to percentage
result_data_agg['percentage'] = 0
for i in range(len(result_data_agg)):
    result_data_agg['percentage'].iloc[i] = (
        (result_data_agg['count'].iloc[i])/count)*100

result_data_agg.sort_values('number', inplace=True, ascending=True)

result = result_data_agg[['number', 'percentage']]

# Now create a Html table with number and its corresponding percentage as columns
covid_data_html_table = result.to_html(index=False)

# Draw and save the graph along with time_stamp with Percentage on Y-axis and Numbers of X-axis
fig = plt.figure()
y_pos = np.arange(len(result_data_agg['number']))
plt.bar(y_pos, result_data_agg['percentage'], align='center', alpha=0.5)
plt.xticks(y_pos, result_data_agg['number'])
plt.ylabel("Percentage")
plt.title("Fraud detection for covid-19 death data")
plt.savefig("output/covid_fraud_visualization" +
            str(datetime.now().timestamp())+".png")


#  Send email with the table and the graph t.aashish.101@gmail.com

fromaddr = "thotaaashish10@gmail.com"
toaddr = ["shivkumarsagshi@gmail.com", "t.aashish.101@gmail.com"]

# instance of MIMEMultipart
msg = MIMEMultipart()

# storing the senders email address
msg['From'] = fromaddr

# storing the receivers email address
msg['To'] = ", ".join(toaddr)

# storing the subject
msg['Subject'] = "Covid Fraud Detection Data"

# string to store the body of the mail
body = "Hi,\n This is Jarvis! Here is your covid fraud detection data as of " + \
    str(datetime.date(datetime.now())) + \
    ". Please find the COVID numbers and the attachment. \n "
body_ending = "\n Thank you"
# attach the body with the msg instance
msg.attach(MIMEText(body, 'plain'))
msg.attach(MIMEText(covid_data_html_table, 'html'))
msg.attach(MIMEText(body_ending, 'plain'))
# * means all if need specific format then *.csv
list_of_files = glob.glob('output/*')
latest_file = max(list_of_files, key=os.path.getctime)


# open the file to be sent
filename = latest_file
print(filename)
attachment = open(filename, "rb")

# instance of MIMEBase and named as p
p = MIMEBase('application', 'octet-stream')

# To change the payload into encoded form
p.set_payload((attachment).read())

# encode into base64
encoders.encode_base64(p)

p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

# attach the instance 'p' to instance 'msg'
msg.attach(p)

# creates SMTP session
s = smtplib.SMTP('smtp.gmail.com', 587)

# start TLS for security
s.starttls()

# Authentication
# add your password here
s.login(fromaddr, "yourpassword")

# Converts the Multipart msg into a string
text = msg.as_string()

# sending the mail
s.sendmail(fromaddr, toaddr, text)

# terminating the session
s.quit()
print("task completed successfully")
