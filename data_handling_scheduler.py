"""
This script handles the scheduled extraction and deletion of gmail emails,
archiving of locally stored html emails, and creating a vector store database
if it doesn't exist.
"""

import os
import shutil
import langchain_processing
import fetch_emails
from apscheduler.schedulers.blocking import BlockingScheduler

# Extraction, deletion and embedding (+ adding to vectorstore) should be performed only once a day
def data_handling():
    # Check if email_data_html has emails, if yes -> move to archive
    if any(os.scandir("email_data_html")):
        # Get a list of all files in the source directory
        files = [f for f in os.listdir("email_data_html") if os.path.isfile(os.path.join("email_data_html", f))]

        # Move each file to the destination directory
        for file in files:
            source_file_path = os.path.join("email_data_html", file)
            destination_file_path = os.path.join("email_data_html_archive", file)
            
            # Move the file
            shutil.move(source_file_path, destination_file_path)

    #Download new emails and store in email_data_html
    fetch_emails.download_emails()

    #Delete emails from gmail inbox
    fetch_emails.empty_inbox()

    # Embed new data and add to vectorstore
    langchain_processing.create_vectorstore_index()


scheduler = BlockingScheduler()
scheduler.add_job(data_handling, 'cron', hour=20, minute=0)

# Start the scheduler
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    # Gracefully exit the scheduler when you press Ctrl+C or there's a system exit
    pass
