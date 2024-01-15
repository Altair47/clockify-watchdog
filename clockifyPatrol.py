import requests, json
from config import *
from datetime import datetime, timedelta
from pathlib  import Path
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

test_Mode = False
monitor_Mode = True
exclude_list = EXCLUDE_LIST


def send_mail(message, receiver, file=None):
    port = 587
    smtp_server = "smtp.mandrillapp.com"
    login = MANDRIL_LOGIN  # Replace with your Mandrill login
    password = MANDRIL_API_KEY  # Replace with your Mandrill API key


    # Construct the email body
    body = f"{message}\n"

    # Create a MIME object
    email_message = MIMEMultipart()
    email_message['From'] = SENDER_EMAIL  # Replace with your sender email
    email_message['To'] = receiver
    email_message['Subject'] = "Clockify Reminder"

    # Attach the message body
    email_message.attach(MIMEText(body, 'plain'))

    # Check if a file is provided and attach it
    if file:
        attachment = open(file, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file)}")
        email_message.attach(part)

    # Convert the email message to string
    email_text = email_message.as_string()

    # Send the email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(login, password)
        server.sendmail(SENDER_EMAIL, receiver, email_text)

    print('Sent')


def GetWorkspaceId():
    # Endpoint URL
    url = "https://api.clockify.me/api/v1/workspaces"

    # Headers with API key
    headers = {
        "X-Api-Key": CLOCKIFY_APIKEY,
    }

    # Send GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        workspaces = response.json()

        # Print workspace details
        for workspace in workspaces:
            print(f"Workspace ID: {workspace['id']}")
            print(f"Workspace Name: {workspace['name']}")
            print("--------")
    else:
        print(f"Error: {response.status_code} - {response.text}")

    return workspaces


def GetUsers():
    # Endpoint URL
    url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACEID}/users"

    # Headers with API key
    headers = {
        "X-Api-Key": CLOCKIFY_APIKEY,
    }

    params = {
        "status": "ACTIVE",
        "page-size": 200,
    }

    # Send GET request
    response = requests.get(url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        users = response.json()

        # Print user details
        for user in users:
            print(f"User ID: {user['id']}")
            print(f"User Name: {user['name']}")
            print(f"User Email: {user['email']}")
            print("--------")
        return users
    else:
        print(f"Error: {response.status_code} - {response.text}")


def GetUserWork(start_date=datetime(2023, 5, 29)):
    user_id = CLOCKIFY_TEST_USER

    # Calculate end date (current date)
    end_date = datetime.now()

    # Endpoint URL
    url = f"https://api.clockify.me/api/v1/workspaces/{WORKSPACEID}/user/{user_id}/time-entries"

    # Headers with API key
    headers = {
        "X-Api-Key": CLOCKIFY_APIKEY,
    }

    # Query parameters
    params = {
        "start": start_date.isoformat() + "Z",
        "end": end_date.isoformat() + "Z",
    }

    # Send GET request
    response = requests.get(url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        time_entries = response.json()

        total_time = timedelta()  # Initialize total time as timedelta

        # Iterate over time entries and calculate total time
        for entry in time_entries:
            start_time = datetime.fromisoformat(entry['timeInterval']['start'])
            end_time = datetime.fromisoformat(entry['timeInterval']['end'])
            time_diff = end_time - start_time
            total_time += time_diff

            print(f"Time Entry ID: {entry['id']}")
            print(f"User ID: {entry['userId']}")
            print(f"Description: {entry['description']}")
            print(f"Start Time: {start_time}")
            print(f"End Time: {end_time}")
            print("--------")

        # Print total time worked
        print(f"Total Time Worked: {total_time.total_seconds()/3600}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def GetUserTimes(user_id):
    api_key = CLOCKIFY_APIKEY
    workspace_id = WORKSPACEID

    # Calculate the start date for this week until now yesterday
    today = datetime.now() # Current Date/Time
    yesterday = datetime.now() - timedelta(days=today.weekday()+1)
    start_date_of_week = yesterday - timedelta(days=yesterday.weekday(),hours=yesterday.hour, minutes=yesterday.minute, seconds=yesterday.second, microseconds=yesterday.microsecond) # 00:00:00 Monday of last week
    end_date_of_week = start_date_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59) # 23:59:59 Friday last week
    end_date = datetime(today.year, today.month, today.day, 23, 59, 59) - timedelta(days=1) # Last second of yesterday

    # Calculate the start and end dates for today
    start_date_yesterday = datetime(today.year, today.month, today.day, 0, 0, 0) - timedelta(days=1)

    # Endpoint URL
    url = f"https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user_id}/time-entries"
    # Headers with API key
    headers = {
        "X-Api-Key": api_key,
    }

    # Query parameters for this week
    params_week = {
        "start": start_date_of_week.date().isoformat() + "T00:00:00Z",
        "end": end_date_of_week.isoformat() + "Z",
        "page-size": 1000,
    }

    # Query parameters for today
    params_today = {
        "start": start_date_yesterday.isoformat() + "Z",
        "end": end_date.isoformat() + "Z",
        "page-size": 1000,
    }

    # Function to get all time entries
    def get_all_time_entries(url, headers, params):
        time_entries = []

        while True:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                entries = response.json()
                time_entries.extend(entries)

                # TO DO : fix for paging changes, now has page size
                # Handle API Pagination:
                # Check for a 'next' page link in the API response headers.If found, extract the URL
                # and continue fetching subsequent pages of results. Break the loop when there are
                # no more pages to retrieve, ensuring that all available data is collected.
                if 'next' in response.links.keys():
                    url = response.links['next']['url']
                    continue
                else:
                    break

            else:
                print(f"Error: {response.status_code} - {response.text}")
                break

        return time_entries

    # Get all time entries for this week
    time_entries_week = get_all_time_entries(url, headers, params_week)

    # Get all time entries for today
    time_entries_today = get_all_time_entries(url, headers, params_today)

    total_time_week = timedelta()  # Initialize total time for this week as timedelta
    total_time_today = timedelta()  # Initialize total time for today as timedelta

    # Iterate over time entries for this week and calculate total time
    for entry in time_entries_week:
        try:
            start_time = datetime.fromisoformat(entry['timeInterval']['start'])
            end_time = datetime.fromisoformat(entry['timeInterval']['end'])
        except:
            continue
        time_diff = end_time - start_time
        total_time_week += time_diff

    # Iterate over time entries for today and calculate total time
    for entry in time_entries_today:
        try:
            start_time = datetime.fromisoformat(entry['timeInterval']['start'])
            end_time = datetime.fromisoformat(entry['timeInterval']['end'])
        except:
            continue
        time_diff = end_time - start_time
        total_time_today += time_diff

    return total_time_today,total_time_week


def convert_timedelta_to_hours_seconds(totalSeconds):
    if totalSeconds == 0:
        return "00:00:00"
    abs_seconds = abs(totalSeconds)
    hours = str(int(abs_seconds // 3600)).zfill(2)
    minutes = str(int((abs_seconds % 3600) // 60)).zfill(2)
    seconds = str(int(abs_seconds % 60)).zfill(2)
    if totalSeconds > 0:
        return (f"{hours}h:{minutes}m:{seconds}s")
    if totalSeconds < 0:
        return (f"+{hours}h:{minutes}m:{seconds}s")


if __name__ == '__main__':
    users = GetUsers() # Call API to get all the users
    yesterdate = datetime.now().date()-timedelta(days=1)
    today = datetime.now() # Current Date/Time
    yesterday = datetime.now() - timedelta(days=1)
    start_date_of_week = yesterday - timedelta(days=yesterday.weekday(),hours=yesterday.hour, minutes=yesterday.minute, seconds=yesterday.second, microseconds=yesterday.microsecond) # 00:00:00 Monday of last week
    end_date_of_week = start_date_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    end_date = datetime(today.year, today.month, today.day, 23, 59, 59) - timedelta(days=1) # Last second of yesterday
    start_date_yesterday = datetime(today.year, today.month, today.day, 0, 0, 0) - timedelta(days=1)

    # Folder handling
    daily_csv_path = "~/clockify/reports_daily/"
    weekly_csv_path = "~/clockify/reports_weekly/"
    daily_csv_path = os.path.expanduser(daily_csv_path)
    daily_csv_path = os.path.normpath(daily_csv_path)
    weekly_csv_path = os.path.expanduser(weekly_csv_path)
    weekly_csv_path = os.path.normpath(weekly_csv_path)
    try:
        os.makedirs(daily_csv_path)
        os.makedirs(weekly_csv_path)
    except Exception as e:
        print(e)

    # Make new file for yesterday.
    with open(f"{daily_csv_path}/{datetime.now().date()}.csv", 'w+') as file1:
        file1.write(f"sep=,\nStart_Date_Of_Yesterday,End_Date_Of_Yesterday,email,id,Day_Filled_Times,Remaining_Time\n")

    # Make new file for last week.
    with open(f"{weekly_csv_path}/{datetime.now().date()}.csv", 'w+') as file1:
        file1.write(f"sep=,\nStart_Date_Of_Week,End_Date_Of_Week,email,id,Week_Filled_Times,Remaining_Time\n")


    for user in users:
        if (datetime.now().weekday() == 6) and not test_Mode:
            exit()

        print(f"\nUser ID: {user['id']}, User Name: {user['name']}, User Email: {user['email']}")
        yesterday_User_Times,week_User_Times = GetUserTimes(user['id']) # Get times for current user iteration

        # Day handling
        if ((datetime.now().weekday() <= 5) and (datetime.now().weekday() >= 1)) or (test_Mode): # Tuesday(1) to Saturday(5)
            if yesterday_User_Times < timedelta(hours=8):
                #Write to file
                if test_Mode or monitor_Mode:
                    try:
                        Day_Filled_Times = convert_timedelta_to_hours_seconds(yesterday_User_Times.total_seconds())
                        Remaining_Time = convert_timedelta_to_hours_seconds((timedelta(hours=8)-yesterday_User_Times).total_seconds())
                        with open(f"{daily_csv_path}/{datetime.now().date()}.csv", 'a') as file1:
                            file1.write(f"{start_date_yesterday},{end_date},{user['email']},{user['id']},{yesterday_User_Times},{Remaining_Time}\n")
                    except Exception as e:
                        print(e)

                if user['email'] in exclude_list: continue
                message = f"Hi {user['name']}! Looks like you forgot to fill your working hours yesterday (between {start_date_yesterday}|{end_date}) on clockify.com please take a bit of time to fill it to 8h"
                print(message)
                if not test_Mode:
                    try:
                        send_mail(message=message,receiver=user['email'])
                    except Exception as e:
                        print(e)
                        continue
        # Week handling
        if (datetime.now().weekday() == 0) or (test_Mode): # Monday(0)
                #Write to file
            if test_Mode or monitor_Mode:
                try:
                    Week_Filled_Times = convert_timedelta_to_hours_seconds(week_User_Times.total_seconds())
                    Remaining_Time = convert_timedelta_to_hours_seconds((timedelta(hours=40)-week_User_Times).total_seconds())
                    with open(f"{weekly_csv_path}/{datetime.now().date()}.csv", 'a') as file1:
                        file1.write(f"{start_date_of_week},{end_date},{user['email']},{user['id']},{Week_Filled_Times},{Remaining_Time}\n")
                except Exception as e:
                    print(e)

            if week_User_Times < timedelta(hours=40):
                message = f"Hi {user['name']}! Looks like you forgot to fill your working hours last week (between {start_date_of_week}|{end_date_of_week}) on clockify.com please take a bit of time to fill it up to 40h"
                print(message)
                if not test_Mode:
                    try:
                        send_mail(message=message,receiver=user['email'])
                    except Exception as e:
                        print(e)
                        continue

    # Send mails when "*.csv"s are populated
    if (datetime.now().weekday() == 0) and not test_Mode:
        for email in REPORTING_MAIL_LIST:
            send_mail(f"Weekly report from {start_date_of_week} to {end_date} !",email,f"{weekly_csv_path}/{datetime.now().date()}.csv")