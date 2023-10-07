import requests, json
from config import *
from datetime import datetime, timedelta

import smtplib

def send_mail(message,receiver):
    port = 587 
    smtp_server = "smtp.mandrillapp.com"
    login = MANDRIL_LOGIN 
    password = MANDRIL_API_KEY

    sender_email = SENDER_EMAIL
    receiver_email = receiver

    # Construct the email body
    body = f"Hi, {message}!\n"

    # Construct the email headers
    headers = f"Subject: Clockify Reminder\nFrom: {sender_email}\nTo: {receiver_email}\n"

    # Construct the full email message
    email_message = headers + "\n" + body

    # send your email
    with smtplib.SMTP(smtp_server, port) as server:
        server.login(login, password)
        server.sendmail(
            sender_email, receiver_email, email_message
        )

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
    today = datetime.now()# Current Date/Time
    yesterday = datetime.now() - timedelta(days=today.weekday()+1)
    start_date_of_week = yesterday - timedelta(days=yesterday.weekday(),hours=yesterday.hour, minutes=yesterday.minute, seconds=yesterday.second, microseconds=yesterday.microsecond)  # 00:00:00 Monday of last week
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

    ''' DEPRECATED
    timeWeek   = total_time_week.total_seconds()     # Seconds
    timeWeekH  = timeWeek // 3600                    # To Hours
    timeWeekM  = timeWeek % 3600 / 60                # To Minutes
    timeWeekR  = 144000 - timeWeek                   # To Minutes
    timeToday  = total_time_today.total_seconds()
    timeTodayH = timeToday // 3600                   # To Hours
    timeTodayM = timeToday % 3600 / 60               # To Minutes
    timeTodayR = 144000 - timeToday
    '''

    # Print the dates and total hours worked this week and today
    #print("|--WEEK STATS--")
    #print(f"    Start Date of This Week: {start_date_of_week.date()}")
    #print(f"    End Date of This Week: {end_date.date()}")
    #print(f"    Total Hours Worked This Week (Monday-Yesterday): {total_time_week} hours")
    #print("|--YESTEDAY STATS--")
    #print(f"    Start Time of Yesterday: {start_date_yesterday}")
    #print(f"    End Date of Yesterday: {end_date}")
    #print(f"    Total Hours Worked Yesterday: {total_time_today} hours")
    #print(f"| Runtime date: {today}")

    return total_time_today,total_time_week


test_Mode = False
monitor_Mode = True
if __name__ == '__main__':
    users = GetUsers()
    yesterdate = datetime.now().date()-timedelta(days=1)
    today = datetime.now()# Current Date/Time
    yesterday = datetime.now() - timedelta(days=1)
    start_date_of_week = yesterday - timedelta(days=yesterday.weekday(),hours=yesterday.hour, minutes=yesterday.minute, seconds=yesterday.second, microseconds=yesterday.microsecond)  # 00:00:00 Monday of last week
    end_date_of_week = start_date_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    end_date = datetime(today.year, today.month, today.day, 23, 59, 59) - timedelta(days=1) # Last second of yesterday
    start_date_yesterday = datetime(today.year, today.month, today.day, 0, 0, 0) - timedelta(days=1)
    
    for user in users:
        if (datetime.now().weekday() == 6) and (test_Mode):
            exit()

        print(f"\nUser ID: {user['id']}, User Name: {user['name']}, User Email: {user['email']}")
        yesterday_User_Times,week_User_Times = GetUserTimes(user['id'])
        if (datetime.now().weekday() <= 5) and (datetime.now().weekday() >= 1) or (test_Mode): #Tuesday(0) to Saturday(5)
            if yesterday_User_Times < timedelta(hours=8):
                #print(f"User: {user['name']},({user['email']}),({user['id']}) has not filled yesterday's ({start_date_yesterday}|{end_date}) 8 hour shift. {yesterday_User_Times} filled")

                if test_Mode or monitor_Mode:
                    with open("Day.txt", 'a') as file1:
                        file1.write(f"{start_date_yesterday}|{end_date}	{user['email']}	{user['id']}	{yesterday_User_Times},	Remaining:{timedelta(hours=8)-yesterday_User_Times}\n")

                message = f"{user['name']}! Looks like you forgot to fill your working hours yesterday (between {start_date_yesterday}|{end_date}) on clockify.com please take a bit of time to fill it to 8h"
                print(message)
                try:
                    send_mail(message,{user['email']})
                except Exception as e:
                    print(e)
                    continue
        if (datetime.now().weekday() == 0) or (test_Mode): #Monday(0)
            if week_User_Times < timedelta(hours=40):
                #print(f"User: {user['name']},({user['email']}),({user['id']}) has not filled this week's 40 hour shift. {week_User_Times} filled")

                if test_Mode or monitor_Mode:
                    with open("Week.txt", 'a') as file1:
                        file1.write(f"{start_date_of_week}-{yesterday}	{user['email']}	{user['id']}	{week_User_Times},	Remaining:{timedelta(hours=40)-week_User_Times}\n")

                message = f"{user['name']}! Looks like you forgot to fill your working hours last week (between {start_date_of_week}|{end_date_of_week}) on clockify.com please take a bit of time to fill it up to 40h"
                print(message)
                try:
                    send_mail(message,{user['email']})
                except Exception as e:
                    print(e)
                    continue